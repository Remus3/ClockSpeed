"""The synthetic save byte builder every phase 4 slice tests against.

WHY THIS SLICE EXISTS BEFORE ANY PARSER DOES
----------------------------------------------
``clockspeed/save/`` is empty. Nothing in this module imports from it, and
``tests/save/test_synthetic.py`` asserts that mechanically, because the ordering
is the point: the corpus is built and independently verified FIRST, and the
parser is then written against verified bytes.

The inverse order is the stated common-mode risk of the whole phase. If the byte
layout here is wrong, every downstream module is written against the same wrong
bytes, every test is green, and the phase closes on a parser that has never seen
a real save. ``memory/test-quality-failure-classes.md`` names the mechanism - a
fixture built parallel to the implementation stays green through the real defect
- and CLAUDE.md section 5 names why it stays invisible: agreement between two
agents is not evidence.

Two controls answer that, and both live in the test module rather than here, so
that neither is graded by the code it grades. See its docstring.

NO REAL SAVE DATA IS IN THIS FILE, BY CONSTRUCTION
----------------------------------------------------
Every string below is invented and obviously synthetic. Every world token is a
made-up 22-character base64url literal beginning ``Clockspeed``. There is no
account id, no world name, no session name, no player display name, no absolute
path and no home directory anywhere in this file, and the test module asserts
several of those directly (non-negotiables 3 and 11).

The options string is the field that carries platform, account and player
display name in plaintext in a REAL save, which is why non-negotiable 12 makes
it redaction-by-default for the parser. The synthetic one carries a ``?`` so a
layout probe can find it by shape, and carries nothing else.

WHAT IS MEASURED HERE AND WHAT IS MODELLED
--------------------------------------------
This distinction is load-bearing and is repeated at each site below. A reader
who cannot tell the two apart will eventually harden a guess into a fact.

MEASURED - taken from the live library by a planner and independently
re-derived by the merger with a second probe, both runs agreeing:

- the string-count split by header version, and that the save name is the string
  header 14 adds at the FRONT,
- the fixed block's field order and widths,
- the 28-byte header tail on 13 and 14, and its absence on 10,
- both chunk framings, including the zlib stream landing at magic+49 with the
  algorithm byte and magic+48 without it,
- the body length prefix: an int64 equal to body length minus 8 on headers 13
  and 14, and an int32 equal to body length minus 4 on header 10. CORRECTED
  2026-08-14 (CS-404) - an earlier revision recorded the prefix as ABSENT on
  header 10, which was a property of this fixture and not of the format,

- the transform deltas for save versions 36, 52 and 60,

- ADDED 2026-08-14 (CS-407) the LEVELLED BODY LAYOUT for header 10 / save 36 -
  a level count, then that many named levels, then one unnamed persistent
  level, then a trailing int32. Measured against a real body by the only
  oracle that cannot be argued with: the walk lands on its exact final byte,
  202 levels and 25769 records later. See LEVELLED_LAYOUT_PAIRS.

- ADDED 2026-08-14 (CS-407) the COMPONENT record grammar - four strings, no
  transform block. See :class:`SyntheticComponent`.

- ADDED 2026-08-15 (CS-404) the USMAP SHIPPED INNER GRAMMAR and the version-1
  VERSIONING BLOCK, both read out of the shipped mapping file. The inner
  grammar is settled by the only oracle that cannot be argued with: walking the
  real file's name, enum and schema sections with it lands EXACTLY on the
  four-character tag that opens the trailing extension container, and all 20
  single-field perturbations of it - every payload-shape drop, every
  payload-shape swap, every field width, and driving the entry loop from the
  property count instead of the serializable count - fail to land there. See
  :data:`USMAP_PROPERTY_PAYLOAD` and ``build_usmap(shipped=True)``.

MODELLED - a self-consistent construction, NOT a measurement:

- the 28 tail bytes' internal structure (only the WIDTH is measured),
- the object record's own field layout (only the DELTA is measured),
- the order within the duplicated size pair,
- the empty-string encoding,
- the usmap inner grammar as written by ``build_usmap(shipped=False)``, which
  is still the DEFAULT. CS-404 measured the real grammar and added it as a
  mode rather than replacing this one, because fixtures across the corpus are
  built on the placeholder. Passing a test built on the default is evidence
  about a loader's container handling and its name section; it is NOT evidence
  that anything can read a real mapping file. ``shipped=True`` carries that
  second claim,
- the CONTENT of an object payload in the levelled layout (only its int32
  length framing is measured).

Each is flagged again where it is built.

THE FLAT BODY LAYOUT IS NOT A REAL LAYOUT, AND STAYS ANYWAY
-------------------------------------------------------------
``build_body`` writes an int32 record count followed by records, with no
preamble. CS-407 measured that NO real body is shaped that way. It is kept, and
every fixture built on it is kept, because those fixtures pin offset arithmetic
and version dispatch - SAVE_CROSS in particular - and moving them would put a
large body of existing assertions on new bytes for no gain. What changed is the
CLAIM: passing a test built on ``build_body`` is evidence about dispatch, and is
not evidence that anything can read a real save. ``build_levelled_body`` is what
carries that second claim, and only for the pairs in LEVELLED_LAYOUT_PAIRS.
"""

from __future__ import annotations

import struct
import zlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

# ---------------------------------------------------------------------------
# Little-endian primitives
# ---------------------------------------------------------------------------


def _i8(value: int) -> bytes:
    """Pack a signed 8-bit integer."""
    return struct.pack("<b", value)


def _i32(value: int) -> bytes:
    """Pack a signed 32-bit integer."""
    return struct.pack("<i", value)


def _u32(value: int) -> bytes:
    """Pack an unsigned 32-bit integer."""
    return struct.pack("<I", value)


def _i64(value: int) -> bytes:
    """Pack a signed 64-bit integer."""
    return struct.pack("<q", value)


def _f32(value: float) -> bytes:
    """Pack a 32-bit float.

    Floats ARE legal in this file. Non-negotiable 6 bans them from the SOLVE
    path, and the static AST gate's pinned module set is the solve package. An
    actor transform is genuinely float data on the wire, and encoding it as
    anything else would be a fixture that lies about the format.
    """
    return struct.pack("<f", value)


def fstring(text: str, *, wide: bool = False) -> bytes:
    """Encode one length-prefixed string.

    The int32 count INCLUDES the trailing null. A POSITIVE count means UTF-8
    with a one-byte null. A NEGATIVE count means UTF-16-LE, and its magnitude is
    the CHARACTER count including a two-byte null - characters, not bytes, which
    is the trap: a parser that treats the magnitude as a byte count reads half
    the string and lands the cursor in the middle of the next field.

    MODELLED, not measured: the empty string is encoded as a bare zero count
    with NO payload. That is the Unreal convention, and it is the one field
    shape here that no probe confirmed. ``mod_metadata`` defaults to empty, so
    this path is exercised by every fixture.

    Args:
        text: The text to encode. ASCII in every call site in this file.
        wide: Encode UTF-16-LE with a negative count instead of UTF-8.

    Returns:
        The encoded string.
    """
    if not text:
        return _i32(0)
    if wide:
        return _i32(-(len(text) + 1)) + text.encode("utf-16-le") + b"\x00\x00"
    raw = text.encode("utf-8")
    return _i32(len(raw) + 1) + raw + b"\x00"


# ---------------------------------------------------------------------------
# Synthetic content. Nothing here resembles a real world, account or player.
# ---------------------------------------------------------------------------

#: The generic level name a real save also carries. It is a GAME CONSTANT rather
#: than personal data, and the shape anchor finds the map-name slot by matching
#: it, so it must be spelled exactly.
MAP_NAME: Final = "Persistent_Level"

SYNTHETIC_SAVE_NAME: Final = "SyntheticSaveName"
SYNTHETIC_SESSION_NAME: Final = "Synthetic Session"

#: The options string. In a REAL save this field carries platform, account and
#: player display name in plaintext, which is what non-negotiable 12 exists for.
#: This one carries a ``?`` so a probe can find it by shape, and nothing else.
SYNTHETIC_OPTIONS: Final = "?listenServer=0?synthetic=1"

#: An INVENTED 22-character base64url world token. Not a real token, and no real
#: token is ever written into this repo (CLAUDE.md section 7 - the advice ledger
#: is keyed by this field, which is exactly why the synthetic one must be fake
#: and obviously so).
#:
#: S105 is suppressed with its code rather than blanket-ignored (PGH bans a
#: bare noqa). Bandit sees a token-shaped literal and cannot tell an invented
#: one from a real secret. This IS the invented one, and the rule that keeps it
#: honest is the test asserting every corpus token starts with ``Clockspeed`` -
#: a real world token never would.
SYNTHETIC_WORLD_TOKEN: Final = "ClockspeedSynthToken00"  # noqa: S105

#: A second invented token, for a slice that needs two distinct worlds.
SYNTHETIC_WORLD_TOKEN_B: Final = "ClockspeedSynthToken01"  # noqa: S105

#: The class path of an actor the registry deliberately does not model.
#: Non-negotiable 7: unknown content is flagged and skipped, never fatal.
UNKNOWN_ACTOR_CLASS_PATH: Final = (
    "/Synthetic/Unknown/Build_SyntheticUnknown.Build_SyntheticUnknown_C"
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

HEADER_VERSION_10: Final = 10
HEADER_VERSION_13: Final = 13
HEADER_VERSION_14: Final = 14

#: Header 14 adds the save name at the FRONT of the string block.
HEADER_VERSION_WITH_SAVE_NAME: Final = 14

#: Headers 13 and 14 carry a 28-byte tail after the identifier.
HEADER_VERSION_WITH_TAIL: Final = 13

#: MEASURED as a WIDTH only. The 28 bytes' internal structure is UNMEASURED, so
#: the filler below is a fixed synthetic pattern with no claimed field meaning.
#: A slice that starts decoding fields out of it is decoding an invention.
HEADER_TAIL_SIZE: Final = 28
SYNTHETIC_TAIL: Final = bytes(range(HEADER_TAIL_SIZE))

UNSUPPORTED_HEADER_VERSION: Final = 99


def build_header(  # noqa: PLR0913 - one keyword per header field is the clearest surface
    *,
    header_version: int = HEADER_VERSION_14,
    save_version: int = 60,
    build_changelist: int = 0,
    save_name: str = SYNTHETIC_SAVE_NAME,
    map_name: str = MAP_NAME,
    options: str = SYNTHETIC_OPTIONS,
    session_name: str = SYNTHETIC_SESSION_NAME,
    play_duration: int = 0,
    datetime_ticks: int = 0,
    visibility: int = 0,
    editor_object_version: int = 40,
    mod_metadata: str = "",
    is_modded: int = 0,
    world_token: str = SYNTHETIC_WORLD_TOKEN,
    tail: bytes | None = None,
    with_save_name: bool | None = None,
    with_tail: bool | None = None,
) -> bytes:
    """Build a save header.

    THE TWO SWITCHES ARE INDEPENDENT PARAMETERS ON PURPOSE. By default the save
    name is emitted when ``header_version >= 14`` and the tail when
    ``header_version >= 13``, which is the measured behaviour - but each can be
    forced either way. A builder that hardcoded them off the version would pass
    every fixture in this file and would make a header-14-layout-without-tail
    probe unbuildable, so the independence is a capability rather than a
    decoration.

    Args:
        header_version: 10, 13 or 14 in the fixtures. Drives STRING LAYOUT.
        save_version: Carried in the header and drives the TRANSFORM OFFSET in
            the body. A parser keying both off one field is the defect
            SAVE_CROSS exists to catch, so the two are never conflated here.
        build_changelist: The build the save was written by.
        save_name: Emitted first, on header 14 only. See ``with_save_name``.
        map_name: The level name.
        options: The options string. Synthetic, and carries a ``?``.
        session_name: The session name. Synthetic.
        play_duration: Seconds.
        datetime_ticks: An int64 tick count.
        visibility: An int8 session visibility flag.
        editor_object_version: An int32.
        mod_metadata: A length-prefixed string, empty by default - which
            exercises the zero-count encoding in every fixture.
        is_modded: An int32 flag.
        world_token: The 22-character base64url identifier. Invented.
        tail: The 28 tail bytes. Defaults to :data:`SYNTHETIC_TAIL`, whose
            internal structure is UNMEASURED.
        with_save_name: Force the save name on or off. None derives it.
        with_tail: Force the tail on or off. None derives it.

    Returns:
        The header bytes, ending on the byte before the chunk magic.
    """
    emit_save_name = (
        header_version >= HEADER_VERSION_WITH_SAVE_NAME
        if with_save_name is None
        else with_save_name
    )
    emit_tail = header_version >= HEADER_VERSION_WITH_TAIL if with_tail is None else with_tail

    out = [_i32(header_version), _i32(save_version), _i32(build_changelist)]
    if emit_save_name:
        out.append(fstring(save_name))
    out.append(fstring(map_name))
    out.append(fstring(options))
    out.append(fstring(session_name))

    # The fixed block, identical on every header version.
    out.append(_i32(play_duration))
    out.append(_i64(datetime_ticks))
    out.append(_i8(visibility))
    out.append(_i32(editor_object_version))
    out.append(fstring(mod_metadata))
    out.append(_i32(is_modded))
    out.append(fstring(world_token))

    if emit_tail:
        out.append(SYNTHETIC_TAIL if tail is None else tail)
    return b"".join(out)


# ---------------------------------------------------------------------------
# Chunk framing
# ---------------------------------------------------------------------------

CHUNK_MAGIC: Final = 0x9E2A83C1
MARKER_22: Final = 0x22222222
MARKER_ZERO: Final = 0x00000000
MAX_CHUNK_SIZE: Final = 131072
ALGORITHM_ZLIB: Final = 3

FRAMING_MARKER22_ALGO: Final = "marker22-algo"
FRAMING_ZERO_MARKER_NOALGO: Final = "zero-marker-noalgo"

#: Bytes from the magic to the first byte of the zlib stream.
#: With the algorithm byte:    4 + 4 + 8 + 1 + 8 * 4 = 49.
#: Without it:                 4 + 4 + 8 +     8 * 4 = 48.
#: Both are MEASURED, and both are exactly what the field lists above produce -
#: an internal cross-check that the two descriptions agree.
ZLIB_OFFSET_WITH_ALGO: Final = 49
ZLIB_OFFSET_WITHOUT_ALGO: Final = 48

#: Offset from the magic to the duplicated size block, per framing.
SIZES_OFFSET_WITH_ALGO: Final = 17
SIZES_OFFSET_WITHOUT_ALGO: Final = 16


def build_chunk(payload: bytes, *, framing: str) -> bytes:
    """Frame and zlib-compress one chunk payload.

    MODELLED, not measured: the ORDER inside the duplicated size block. It is
    written here as ``(compressed, uncompressed, compressed, uncompressed)``.
    The brief pinned that the two sizes each appear TWICE and did not pin
    whether the repeat interleaves or follows, so a slice depending on the
    distinction must re-probe rather than trust this.

    The duplication is the format's own consistency check, which is why
    :func:`corrupt_size_disagreement` exists: a parser reading only the first
    copy cannot notice a mismatch, and nothing else in the format would tell it.

    Args:
        payload: The uncompressed body.
        framing: :data:`FRAMING_MARKER22_ALGO` or
            :data:`FRAMING_ZERO_MARKER_NOALGO`.

    Returns:
        The framed chunk, magic first.

    Raises:
        ValueError: The framing is not one of the two measured shapes.
    """
    compressed = zlib.compress(payload)
    sizes = _i64(len(compressed)) + _i64(len(payload)) + _i64(len(compressed)) + _i64(len(payload))
    if framing == FRAMING_MARKER22_ALGO:
        head = _u32(CHUNK_MAGIC) + _u32(MARKER_22) + _i64(MAX_CHUNK_SIZE) + _i8(ALGORITHM_ZLIB)
    elif framing == FRAMING_ZERO_MARKER_NOALGO:
        head = _u32(CHUNK_MAGIC) + _u32(MARKER_ZERO) + _i64(MAX_CHUNK_SIZE)
    else:
        raise ValueError(f"unknown framing: {framing!r}")
    return head + sizes + compressed


def split_payload(payload: bytes, max_chunk_size: int = MAX_CHUNK_SIZE) -> list[bytes]:
    """Split a body into the decompressed slices each chunk carries.

    MEASURED, and measured by THIS SLICE rather than handed to it. The real save
    on the development machine carries 13 chunks whose decompressed payloads are
    131072 bytes each except the last, and whose concatenation is the body. The
    split is on the DECOMPRESSED size, and the int64 body length prefix counts
    toward the first slice.

    Args:
        payload: The whole uncompressed body, length prefix included.
        max_chunk_size: Decompressed bytes per chunk.

    Returns:
        The slices. Always at least one, so an empty body still frames a chunk.
    """
    if not payload:
        return [b""]
    return [payload[at : at + max_chunk_size] for at in range(0, len(payload), max_chunk_size)]


def build_chunks(payload: bytes, *, framing: str, max_chunk_size: int = MAX_CHUNK_SIZE) -> bytes:
    """Frame a body as one OR MORE chunks, exactly as a real save does.

    A real save is multi-chunk - the file measured for this slice has 13 - and a
    chunk walker tested only against a single-chunk corpus would pass its whole
    suite while being unable to read any real save. That is the common-mode
    failure this corpus exists to prevent, so the corpus can express both.

    Args:
        payload: The whole uncompressed body, length prefix included.
        framing: One of the two measured framings.
        max_chunk_size: Decompressed bytes per chunk.

    Returns:
        Every chunk, concatenated.
    """
    return b"".join(
        build_chunk(part, framing=framing) for part in split_payload(payload, max_chunk_size)
    )


def sizes_offset(framing: str) -> int:
    """Offset from the magic to the duplicated size block.

    Args:
        framing: One of the two measured framings.

    Returns:
        17 with the algorithm byte, 16 without it.
    """
    return SIZES_OFFSET_WITH_ALGO if framing == FRAMING_MARKER22_ALGO else SIZES_OFFSET_WITHOUT_ALGO


# ---------------------------------------------------------------------------
# The body and its object records
# ---------------------------------------------------------------------------

#: MEASURED. The byte delta before the transform block, by SAVE version. THIS
#: TABLE SERVES THE FLAT CORPUS ONLY - :data:`LEVELLED_LAYOUTS` below carries
#: the delta for the levelled corpus, keyed on the PAIR.
#:
#: SAVE VERSION 42 CARRIES 4, AND WHAT CHANGED UNDER CS-407 IS THE EVIDENCE,
#: NOT THE VALUE. Two earlier sessions reached 4 and both DISCARDED it, rightly:
#: one because its method could not recover the known deltas for 36 and 60 when
#: validated against them, the other because the reading needed two unmeasured
#: assumptions holding each other up. With 36 giving 4 and 52 giving 8, the
#: value 4 is exactly what "looks derived" produces, so arriving at it is the
#: PRIOR OF THE FAILURE MODE rather than corroboration.
#:
#: What makes it a measurement now is a corroborator independent of section
#: arithmetic: every actor rotation is a unit quaternion, and 17763 of 17763
#: actors in the one real header-13 body give a unit quaternion at shift 4,
#: while the runner-up shift scores 1027 and falls to 2 once scale plausibility
#: is included. The method was validated first by recovering 4 for save 36 and 8
#: for saves 52 and 60.
#:
#: This table is VERSION keyed and is the weaker model, kept because the flat
#: corpus is built on it. :data:`LEVELLED_LAYOUTS` keys the same fact on the
#: PAIR and is authoritative: header version, save version and build changelist
#: are all perfect predictors of every grammar difference in the corpus, so the
#: KEY IS UNDETERMINED, exactly as ``docs/adr/0007`` records for the chunk
#: marker. The two are held in agreement by a test rather than by a convention.
TRANSFORM_DELTA_BY_SAVE_VERSION: Final = {36: 4, 42: 4, 52: 8, 60: 8}

#: Rotation (4) + translation (3) + scale (3), all float32.
TRANSFORM_FLOAT_COUNT: Final = 10
TRANSFORM_BYTES: Final = TRANSFORM_FLOAT_COUNT * 4


class UnmeasuredTransformDeltaError(LookupError):
    """Raised when a body is requested for a save version whose delta is unmeasured.

    A loud failure rather than a fallback. A default here would silently emit
    plausible bytes for save version 42 and every downstream test would agree
    with them.
    """


@dataclass(frozen=True)
class SyntheticObject:
    """One object record.

    MODELLED, not measured: the field layout below. Only the DELTA is carried
    from measurement - its width, not its meaning. The record is therefore a
    valid fixture for OFFSET ARITHMETIC and VERSION DISPATCH, which is what
    SAVE_CROSS tests, and is NOT evidence about the real actor grammar. A slice
    implementing real actor deserialization must probe the record layout
    itself; this is the single largest modelled area in the corpus.

    Transform values are chosen to be exactly representable in float32, so a
    round trip through the wire format cannot introduce a difference that looks
    like a parser bug.
    """

    class_path: str
    root_object: str
    instance_name: str
    rotation: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    translation: tuple[float, float, float] = (128.0, 256.0, 0.5)
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0)
    object_type: int = 1
    was_placed_in_level: int = 1

    def encode(self, delta: int) -> bytes:
        """Encode this record at a given transform delta.

        Args:
            delta: Filler width before the transform block. Opaque: its bytes
                carry no modelled meaning.

        Returns:
            The record bytes.
        """
        return b"".join(
            [
                _i32(self.object_type),
                fstring(self.class_path),
                fstring(self.root_object),
                fstring(self.instance_name),
                bytes(delta),
                b"".join(_f32(v) for v in (*self.rotation, *self.translation, *self.scale)),
                _i32(self.was_placed_in_level),
            ]
        )


def transform_delta(save_version: int) -> int:
    """Look up the measured transform delta for a save version.

    Args:
        save_version: The save version.

    Returns:
        The delta in bytes.

    Raises:
        UnmeasuredTransformDeltaError: No delta has been measured for it.
    """
    try:
        return TRANSFORM_DELTA_BY_SAVE_VERSION[save_version]
    except KeyError:
        raise UnmeasuredTransformDeltaError(
            f"no measured transform delta for save version {save_version};"
            " measure it rather than interpolating from its neighbours"
        ) from None


def build_body(
    objects: list[SyntheticObject] | tuple[SyntheticObject, ...], *, save_version: int
) -> bytes:
    """Build the object section of a body.

    The delta is looked up LAZILY - an empty object list never consults it, so
    SAVE_V42 is constructible at import time despite having no measured delta.

    This function does NOT add the int64 length prefix. That prefix follows the
    HEADER version while the delta follows the SAVE version, and the two live in
    different functions precisely so they cannot be accidentally driven off one
    field. :func:`build_save` adds it.

    Args:
        objects: The records.
        save_version: Drives the transform delta.

    Returns:
        ``int32 count`` followed by the records.

    Raises:
        UnmeasuredTransformDeltaError: Objects were supplied for a save version
            whose delta is unmeasured.
    """
    out = [_i32(len(objects))]
    if objects:
        delta = transform_delta(save_version)
        out.extend(obj.encode(delta) for obj in objects)
    return b"".join(out)


# ---------------------------------------------------------------------------
# The LEVELLED body layout - what a real body actually is
#
# MEASURED under CS-407 against a real header-10 / save-36 body, and measured by
# the only oracle that cannot be argued with: the walk below consumes the body
# and lands EXACTLY on its final byte, 202 levels and 25769 records later, with
# nothing left over. A grammar that is wrong anywhere does not end on the last
# byte; it ends early, late, or inside a string.
#
# It replaces the assumption every earlier phase-4 slice inherited - that a body
# opens with an int32 object count. It does not. A real body opens with a
# version-dependent preamble and then carries a LIST OF LEVELS, each with its
# own record table. That is why `build_body` above produces bytes no real save
# has ever contained, and why the fixtures built from it prove offset arithmetic
# and version dispatch and nothing else.
#
# THIS LAYOUT IS MEASURED FOR HEADER 10 / SAVE 36 AND FOR NO OTHER PAIR. The
# other three real pairs are recorded in LEVELLED_LAYOUT_UNMEASURED below with
# what was and was not established about each. Widening this builder to cover
# one of them is a MEASUREMENT against a real save of that version, never an
# interpolation from this one.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# The four pairs' SKELETON grammars
#
# READ THE WORD SKELETON. Roughly three quarters of every real body is opaque
# property payload this grammar does not describe - 69.5% to 77.7% across the
# eight real save-52 files, and 12100463 of 18086289 bytes on the one real
# save-42 file. What is named below is a 1.8% to 2.7% framing skeleton plus its
# length-prefixed strings. "The body SKELETON grammar is closed" is the true
# sentence; "the body grammar is closed" is not, and never becomes true by
# adding pairs.
#
# THE KEY IS THE PAIR, AND THAT IS DELIBERATE. Header version, save version and
# build changelist are all PERFECT predictors of every difference in the table
# below, because each header version occurs with exactly one set of save
# versions in the corpus. Nothing separates them, so nothing here claims one is
# the key - the same undetermined keying docs/adr/0007 records for the chunk
# marker. Writing "save 36 uses 4-byte sizes" would assert a key the evidence
# does not support, and clockspeed/save/objects.py records that this exact
# mistake was made once already and was corrected under CS-404.
# ---------------------------------------------------------------------------

#: A named level closes on nothing after its data section.
LEVEL_TAIL_NONE: Final = "none"

#: A named level closes on one int32. Position and width only; no meaning.
LEVEL_TAIL_WORD: Final = "word"

#: A named level closes on 12 constant bytes and then a package summary.
LEVEL_TAIL_SUMMARY: Final = "summary"

#: CONSTANT BLOBS, SKIPPED BY LENGTH ON BOTH SIDES, exactly as BOOTSTRAP.md
#: already does for the 28-byte header tail. No boundary inside any of these is
#: observable in the corpus, so none is claimed.
#:
#: The 70-byte run before a package summary's count is the sharpest case: every
#: candidate split was tried and NONE is supported - not 4+6, not 8+2, not
#: 16+10. Every head int32 has exactly one distinct value across the corpus and
#: the trailing run has one, so the interior is unfalsifiable rather than
#: merely unmeasured. The count at +70 and the 20-byte entry ARE pinned: they
#: are the unique surviving (F, K) over F in [0,84) x K in [1,256], robust to
#: three plausibility caps and over-determined by four distinct counts against
#: four distinct widths.
#:
#: THE FIXTURE WRITES ZEROS INTO EVERY ONE OF THESE. It therefore cannot be
#: evidence about their contents, only about their widths - which is all the
#: parser reads.
PACKAGE_SUMMARY_HEAD_BYTES: Final = 70
CUSTOM_VERSION_ENTRY_BYTES: Final = 20
SECTION_SIZE_WIDTH_WIDE: Final = 8
SECTION_SIZE_WIDTH_NARROW: Final = 4
LEVEL_TAIL_CONSTANT_BYTES: Final = 12
DATA_ENTRY_LEAD_BYTES: Final = 8
GRID_OPAQUE_BYTES: Final = 8
GRID_CELL_OPAQUE_BYTES: Final = 4
COMPONENT_PRE_WORD_BYTES: Final = 4


@dataclass(frozen=True)
class LevelledLayout:
    """Every way one measured pair's body skeleton differs from another's.

    Attributes:
        transform_delta: The opaque run between an actor's instance name and
            its transform block. A LIVE field, not filler - it takes 8 distinct
            values with only bits 3, 6, 19, 21 and 32 ever set, which is a bit
            mask rather than an integer. Only its WIDTH is read.
        section_size_width: 4 or 8. An 8-byte size is written as an int32 size
            followed by an int32 reserved word - see :func:`section_size`.
        package_summary: The body opens with a package summary.
        grid_preamble: The body carries the grid block before the level count.
        data_entry_lead: Opaque bytes before each payload's length prefix.
        data_entry_trailer: Each payload is followed by an int32.
        component_pre_word: A component carries 4 opaque bytes before its
            parent path, where the other pairs go straight to the string.
        level_tail: One of the three ``LEVEL_TAIL_*`` constants, applied to
            NAMED levels only.
        second_collectables_named: Named levels close with a second collectable
            block. The persistent level always does.
    """

    transform_delta: int
    section_size_width: int
    package_summary: bool
    grid_preamble: bool
    data_entry_lead: int
    data_entry_trailer: bool
    component_pre_word: bool
    level_tail: str
    second_collectables_named: bool


#: The (header version, save version) pairs whose whole-body SKELETON is
#: MEASURED, with the grammar each one uses. A pair is added here only after a
#: real body of that pair walks to its exact final byte with nothing left over.
#:
#: Landings behind this table, from the merger's own runs against real files:
#: (10,36) 3 of 3 exact, (13,42) 1 of 1, (14,52) 8 of 8, (14,60) 2 of 2.
#:
#: READ THOSE COUNTS AS FILE COUNTS, NOT AS INDEPENDENCE COUNTS. (13,42) is one
#: file. (14,60)'s two bodies are byte-identical from offset 4 through 150074,
#: which is exactly where the persistent level starts, so the preamble, the grid
#: block, the level tail and all 187 named levels are n=1 and only the
#: persistent level's contents are genuinely n=2. (14,52)'s eight files share a
#: byte-identical 69750-byte preamble - it is the static world-partition grid,
#: so n=1 there is a CEILING rather than a sampling accident - and collapse to
#: six distinct structural signatures, of which the entire no-header-block
#: branch lives in ONE file.
LEVELLED_LAYOUTS: Final = {
    (10, 36): LevelledLayout(
        transform_delta=4,
        section_size_width=4,
        package_summary=False,
        grid_preamble=False,
        data_entry_lead=0,
        data_entry_trailer=False,
        component_pre_word=False,
        level_tail=LEVEL_TAIL_NONE,
        second_collectables_named=True,
    ),
    (13, 42): LevelledLayout(
        transform_delta=4,
        section_size_width=8,
        package_summary=False,
        grid_preamble=True,
        data_entry_lead=DATA_ENTRY_LEAD_BYTES,
        data_entry_trailer=False,
        component_pre_word=False,
        level_tail=LEVEL_TAIL_NONE,
        second_collectables_named=True,
    ),
    (14, 52): LevelledLayout(
        transform_delta=8,
        section_size_width=8,
        package_summary=False,
        grid_preamble=True,
        data_entry_lead=DATA_ENTRY_LEAD_BYTES,
        data_entry_trailer=False,
        component_pre_word=True,
        level_tail=LEVEL_TAIL_WORD,
        second_collectables_named=True,
    ),
    (14, 60): LevelledLayout(
        transform_delta=8,
        section_size_width=8,
        package_summary=True,
        grid_preamble=True,
        data_entry_lead=DATA_ENTRY_LEAD_BYTES,
        data_entry_trailer=True,
        component_pre_word=True,
        level_tail=LEVEL_TAIL_SUMMARY,
        second_collectables_named=False,
    ),
}

#: The pairs above, in declaration order.
LEVELLED_LAYOUT_PAIRS: Final = tuple(LEVELLED_LAYOUTS)

#: EMPTY, and that is the CS-407 result: all four real pairs now have a measured
#: body skeleton. It is kept rather than deleted because it is the structure a
#: later slice resumes from, and a fifth pair arriving with an underived layout
#: belongs here rather than in a sentence somewhere.
#:
#: WHAT REMAINS UNMEASURED IS NO LONGER A PAIR - it is a set of SPANS inside
#: pairs that do parse, and those are recorded in
#: :data:`LEVELLED_LAYOUT_OPAQUE_SPANS` so a later slice can execute against
#: them. A partial recorded as prose is not resumable; a partial recorded as a
#: structure is.
LEVELLED_LAYOUT_UNMEASURED: Final[dict[tuple[int, int], str]] = {}

#: WHAT THE SKELETON DOES NOT DESCRIBE, as a structure rather than an adjective.
#: Each entry is a span the walk steps over by LENGTH, with the width that is
#: pinned and the claim that is NOT made about its interior. A later slice
#: measuring one of these executes against this table.
LEVELLED_LAYOUT_OPAQUE_SPANS: Final = {
    "transform_delta": (
        "the run between an actor's instance name and its transform block. Its "
        "WIDTH is pinned per pair by the quaternion check, and by nothing else: "
        "pre-runs of 0, 4, 8 and 12 bytes ALL land byte-exact on all 8 real "
        "save-52 files, so byte arithmetic is blind even to the width. Splitting "
        "it into named int32 fields is refuted outright - it takes 8 distinct "
        "values with only bits 3, 6, 19, 21 and 32 ever set, which is a bit mask"
    ),
    "package_summary_head": (
        "70 bytes before the custom-version count. NO interior boundary is "
        "observable - not 4+6, not 8+2, not 16+10. Includes a 44-byte run "
        "consistent with a length-prefixed string of declared length 40 on all "
        "188 instances, never exercised with a second length"
    ),
    "custom_version_entry": (
        "20 bytes per entry. The count and the width are jointly pinned as the "
        "unique surviving (70, 20); the interior of one entry is not"
    ),
    "level_tail_constant": (
        "12 bytes closing a named level on the (14,60) pair. Its START is pinned "
        "by the declared data-section size; its WIDTH of 12 is pinned only "
        "transitively - 41 distinct splits survive consumption alone"
    ),
    "data_entry_lead": (
        "8 bytes before each payload's length. On (13,42) they take exactly two "
        "joint values, (42,0) and (36,1), so a two-int32 split has field 1 "
        "perfectly determined by field 0; on (14,52) the second word is "
        "collinear with the first across 29466 entries. An int64 reading closes "
        "byte-exactly too. The SPLIT is unfalsifiable; the 8-byte width is not"
    ),
    "component_pre_word": (
        "4 bytes before a component's parent path on (14,52) and (14,60). The "
        "WIDTH is pinned decisively - 0-byte, 8-byte and empty-string rivals all "
        "land 0 of 8 - and the TYPE is not: a two-int16 reading closes exactly"
    ),
    "section_size_reserved": (
        "the second int32 of an 8-byte section size. Zero in 5890 of 5890 "
        "instances on (14,52) and in every instance elsewhere, and the largest "
        "section observed is 0.45% of 2^31, so int64 and int32-plus-reserved are "
        "undecidable now and permanently. Read as int32-plus-reserved and FLAG a "
        "non-zero reserved word - see the parser's rationale"
    ),
    "grid_opaque": (
        "8 bytes per grid and 4 per cell. Labels like cell_size and hash are "
        "unsupported - one observed value is 12798, which is not a plausible "
        "round cell size"
    ),
    "object_data_payload": (
        "the property payload itself, and it is THREE QUARTERS OF EVERY BODY. "
        "Only its int32 length framing is measured. This is the largest "
        "unmeasured span in the format by two orders of magnitude"
    ),
}

#: The body's final int32. MEASURED as present and zero on the real header-10
#: body; a walk without it stops four bytes short of the end. Only its PRESENCE
#: and its observed value are measured - nothing here claims to know its meaning.
BODY_TRAILING_INT32: Final = 0


@dataclass(frozen=True)
class SyntheticCollectable:
    """One entry in a level's collectable list.

    MEASURED as a PAIR OF STRINGS, and measured only in the sense that reading
    it as two strings is what makes the whole-body walk land on the final byte.
    No meaning is claimed for either half.
    """

    level_name: str = "Persistent_Level"
    path_name: str = "Persistent_Level:PersistentLevel.SyntheticCollectable_0"

    def encode(self) -> bytes:
        """Encode this collectable.

        Returns:
            The two length-prefixed strings, in file order.
        """
        return fstring(self.level_name) + fstring(self.path_name)


def section_size(value: int, width: int, *, reserved: int = 0) -> bytes:
    """Encode one section size at the pair's width.

    AN 8-BYTE SIZE IS WRITTEN AS AN INT32 SIZE PLUS AN INT32 RESERVED WORD, not
    as an int64. The two are byte-identical while the reserved word is zero -
    which it is in every one of the 5890 instances measured on the (14,52)
    corpus and in every instance elsewhere - so the corpus cannot decide between
    them and never will: the largest section observed is 0.45% of 2^31, so no
    save that can physically exist will set the high word by size.

    The tie is broken on asymmetric damage rather than on taste. If the field
    really is an int64, this reading is correct for every save that can exist.
    If it is int32-plus-reserved and that word ever goes non-zero, an int64
    reader silently computes ``lo + hi * 2**32``, gets an astronomical size, and
    reports a section-size mismatch - a diagnosis pointing at the WRONG FIELD.
    This reading is never worse and sometimes much better.

    ``reserved`` is a parameter so a fixture can drive the non-zero case, which
    is the branch non-negotiable 7 governs: it must be FLAGGED, not crashed on.

    Args:
        value: The section size.
        width: 4 or 8, from the pair's layout.
        reserved: The second word of an 8-byte size. Ignored at width 4.

    Returns:
        The encoded size.
    """
    if width == SECTION_SIZE_WIDTH_WIDE:
        return _i32(value) + _i32(reserved)
    return _i32(value)


@dataclass(frozen=True)
class SyntheticPackageSummary:
    """The block a (14,60) body opens with, and that its named levels close on.

    A 70-BYTE CONSTANT RUN, THEN A COUNT, THEN THAT MANY 20-BYTE ENTRIES. The
    count's position at +70 and the 20-byte entry width are jointly pinned as
    the unique surviving pair over a brute-force search. The 70 bytes are ONE
    BLOB: no interior boundary is observable, so this writes zeros and claims
    nothing about their contents.
    """

    custom_version_count: int = 3

    def encode(self) -> bytes:
        """Encode the summary.

        Returns:
            The constant run, the count, and the entries.
        """
        return b"".join(
            [
                bytes(PACKAGE_SUMMARY_HEAD_BYTES),
                _i32(self.custom_version_count),
                bytes(self.custom_version_count * CUSTOM_VERSION_ENTRY_BYTES),
            ]
        )


@dataclass(frozen=True)
class SyntheticGridCell:
    """One cell of one grid: a name and 4 opaque bytes.

    No label is claimed for the 4 bytes.
    """

    name: str

    def encode(self) -> bytes:
        """Encode the cell.

        Returns:
            The name and the opaque run.
        """
        return fstring(self.name) + bytes(GRID_CELL_OPAQUE_BYTES)


@dataclass(frozen=True)
class SyntheticGrid:
    """One grid of the preamble: a name, 8 opaque bytes, then counted cells.

    The 8 bytes were labelled ``cell_size`` and ``hash`` by an earlier reading
    and neither label survives: one observed value is 12798, which is not a
    plausible round cell size. Only the WIDTH is carried here.
    """

    name: str
    cells: tuple[SyntheticGridCell, ...] = ()

    def encode(self) -> bytes:
        """Encode the grid and its cells.

        Returns:
            The grid bytes.
        """
        return b"".join(
            [
                fstring(self.name),
                bytes(GRID_OPAQUE_BYTES),
                _i32(len(self.cells)),
                *(cell.encode() for cell in self.cells),
            ]
        )


@dataclass(frozen=True)
class SyntheticComponent:
    """One COMPONENT record, in the grammar a real save actually uses.

    MEASURED under CS-407, and it is NOT the actor grammar. A component carries
    a parent path where an actor carries its filler and transform block. The
    corpus previously encoded both kinds identically and labelled the component
    branch unverified; this is the measurement that closes that gap.

    THE TWO PAIRS ON HEADER 14 PUT 4 OPAQUE BYTES BEFORE THAT PATH. That width
    is pinned decisively rather than by consumption alone: a 0-byte rival, an
    8-byte rival and an empty-string rival all land on 0 of the 8 real save-52
    files, so the corpus CAN tell them apart. Its TYPE is not pinned - a
    two-int16 reading closes byte-exactly - so it is written as an opaque run.

    :class:`SyntheticObject` above still encodes the actor grammar under either
    discriminator, deliberately, because the fixtures built on it pin offset
    arithmetic and must not shift underneath the tests that already assert them.
    """

    class_path: str
    root_object: str
    instance_name: str
    parent_object_root: str = "Persistent_Level:PersistentLevel.SyntheticParent_0"
    object_type: int = 0

    def encode(self, *, pre_word: bool = False) -> bytes:
        """Encode this record.

        Args:
            pre_word: Emit the 4 opaque bytes before the parent path.

        Returns:
            The record bytes.
        """
        return b"".join(
            [
                _i32(self.object_type),
                fstring(self.class_path),
                fstring(self.root_object),
                fstring(self.instance_name),
                bytes(COMPONENT_PRE_WORD_BYTES) if pre_word else b"",
                fstring(self.parent_object_root),
            ]
        )


@dataclass(frozen=True)
class SyntheticLevel:
    """One level: a record table, a collectable list, and a payload section.

    ``name`` is None for the PERSISTENT level, which a real body carries once,
    unnamed, after every named level. That asymmetry is measured: a walk that
    expects a name there stops with four hundred thousand bytes unread.

    MODELLED, not measured: the CONTENT of each object payload. Only the framing
    around it - an int32 length then that many bytes - is measured, so the
    payloads here are opaque filler and any slice decoding a field out of one is
    decoding an invention.
    """

    name: str | None
    objects: tuple[SyntheticObject, ...] = ()
    components: tuple[SyntheticComponent, ...] = ()
    #: None means the level's header section ENDS AT THE RECORD TABLE with no
    #: collectable block at all, which is the shape the size-driven rule exists
    #: to handle. An empty tuple still emits a block declaring zero entries.
    collectables: tuple[SyntheticCollectable, ...] | None = ()
    second_collectables: tuple[SyntheticCollectable, ...] = ()
    payload_size: int = 24
    #: The second word of this level's 8-byte section sizes. Non-zero exercises
    #: the flag path; it is zero in every real section measured.
    reserved_word: int = 0
    #: The named level's closing int32 where the layout carries one. Observed
    #: constant; position and width only.
    tail_word: int = 0
    summary: SyntheticPackageSummary = SyntheticPackageSummary()

    @property
    def record_count(self) -> int:
        """How many records this level's table declares.

        Returns:
            The count of actors plus components.
        """
        return len(self.objects) + len(self.components)

    def encode(self, *, layout: LevelledLayout) -> bytes:
        """Encode the whole level in one pair's grammar.

        The two declared sizes are computed from the bytes they cover rather
        than accumulated by hand, so a fixture cannot declare a size that
        disagrees with its own content - which is the exact defect the real
        format's duplicated sizes exist to catch.

        Args:
            layout: The pair's grammar. Drives the transform delta, the size
                width, the data-entry shape, the component shape and the tail.

        Returns:
            The level bytes.

        Raises:
            ValueError: A named level declares a second collectable block under
                a layout that does not emit one. A fixture that declares bytes
                it does not write is the defect class this corpus exists to
                avoid, so it fails loudly rather than dropping them.
        """
        if (
            self.name is not None
            and self.second_collectables
            and not layout.second_collectables_named
        ):
            raise ValueError(
                "this layout emits no second collectable block on a named level,"
                " so declaring one would silently drop it"
            )

        records = b"".join(obj.encode(layout.transform_delta) for obj in self.objects)
        records += b"".join(
            component.encode(pre_word=layout.component_pre_word) for component in self.components
        )
        header_section = _i32(self.record_count) + records
        if self.collectables is not None:
            header_section += _i32(len(self.collectables)) + b"".join(
                item.encode() for item in self.collectables
            )

        # One payload per record, matching the real body, where the data
        # section's count equals the header table's count exactly - 2945 of
        # 2945 levels on the (14,52) corpus.
        payload = bytes(self.payload_size)
        entry = (
            bytes(layout.data_entry_lead)
            + _i32(len(payload))
            + payload
            + (_i32(0) if layout.data_entry_trailer else b"")
        )
        data_section = _i32(self.record_count) + entry * self.record_count

        out: list[bytes] = []
        if self.name is not None:
            out.append(fstring(self.name))
        width = layout.section_size_width
        out.append(section_size(len(header_section), width, reserved=self.reserved_word))
        out.append(header_section)
        out.append(section_size(len(data_section), width, reserved=self.reserved_word))
        out.append(data_section)
        if self.name is not None:
            if layout.level_tail == LEVEL_TAIL_WORD:
                out.append(_i32(self.tail_word))
            elif layout.level_tail == LEVEL_TAIL_SUMMARY:
                out.append(bytes(LEVEL_TAIL_CONSTANT_BYTES))
                out.append(self.summary.encode())
        if self.name is None or layout.second_collectables_named:
            out.append(_i32(len(self.second_collectables)))
            out.extend(item.encode() for item in self.second_collectables)
        return b"".join(out)


class UnmeasuredBodyLayoutError(LookupError):
    """Raised when a levelled body is requested for a pair with no measured layout.

    A loud failure rather than a fallback, for the same reason
    :class:`UnmeasuredTransformDeltaError` is: a default here would emit
    plausible bytes for an underived pair and every downstream test would agree
    with them.
    """


def levelled_layout(header_version: int, save_version: int) -> LevelledLayout:
    """Look up the MEASURED skeleton grammar for a pair.

    Args:
        header_version: The header version.
        save_version: The save version.

    Returns:
        The pair's layout.

    Raises:
        UnmeasuredBodyLayoutError: The pair has no measured layout. Never
            interpolated from a neighbouring pair.
    """
    try:
        return LEVELLED_LAYOUTS[(header_version, save_version)]
    except KeyError:
        raise UnmeasuredBodyLayoutError(
            f"no measured body layout for header {header_version} with save {save_version};"
            " measure it rather than interpolating from another pair"
        ) from None


def build_levelled_body(
    named: tuple[SyntheticLevel, ...],
    persistent: SyntheticLevel,
    *,
    header_version: int,
    save_version: int,
    summary: SyntheticPackageSummary | None = None,
    grids: tuple[SyntheticGrid, ...] = (),
) -> bytes:
    """Build a body in the MEASURED levelled SKELETON layout for one pair.

    This does NOT add the body length prefix, matching :func:`build_body`, so
    that the prefix stays in one function and cannot be driven off the wrong
    field by accident.

    BOTH VERSION SCALARS ARE TAKEN, because the layout is keyed on the PAIR.
    Neither one alone selects a grammar in this corpus: each header version
    occurs with exactly one set of save versions, so both are perfect
    predictors and neither is established as the key.

    Args:
        named: The named levels, in file order.
        persistent: The trailing unnamed level. Its ``name`` must be None.
        header_version: Half of the layout key.
        save_version: The other half.
        summary: The body's opening package summary, where the layout carries
            one. Defaults to a fresh one.
        grids: The grid preamble's grids, where the layout carries one.

    Returns:
        The preamble, the level count, every level, and the trailing int32.

    Raises:
        ValueError: ``persistent`` carries a name, which no real body does.
        UnmeasuredBodyLayoutError: The pair has no measured layout.
    """
    if persistent.name is not None:
        raise ValueError("the persistent level is unnamed in every measured body")
    layout = levelled_layout(header_version, save_version)

    out: list[bytes] = []
    if layout.package_summary:
        out.append((summary or SyntheticPackageSummary()).encode())
    if layout.grid_preamble:
        out.append(_i32(len(grids)))
        out.extend(grid.encode() for grid in grids)
    out.append(_i32(len(named)))
    out.extend(level.encode(layout=layout) for level in named)
    out.append(persistent.encode(layout=layout))
    out.append(_i32(BODY_TRAILING_INT32))
    return b"".join(out)


# ---------------------------------------------------------------------------
# Whole saves
# ---------------------------------------------------------------------------

#: Headers 13 and 14 open the DECOMPRESSED body with an int64 length; 10 does
#: not. MEASURED, and keyed on the HEADER version - never on the save version.
#:
#: WHAT THE INT64 COUNTS, measured by this slice against a real save: the length
#: of the ENTIRE CONCATENATED body across every chunk, excluding the 8 bytes of
#: the prefix itself. On the measured file that is 1574433 against a total
#: decompressed size of 1574441 over 13 chunks.
#:
#: The distinction is invisible in a single-chunk fixture, where "this chunk's
#: payload minus 8" and "the whole body" are the same number. A parser that
#: adopts the former reads exactly one chunk of any real save and reports a
#: truncated world rather than an error. SAVE_MULTICHUNK is the fixture that
#: tells the two apart.
HEADER_VERSION_WITH_BODY_LENGTH: Final = 13

#: Width of the body length prefix, per header version. MEASURED against real
#: saves of every version by decompressing them through the shipped walker.
BODY_PREFIX_WIDTH_WIDE: Final = 8
BODY_PREFIX_WIDTH_NARROW: Final = 4


def body_prefix_width(header_version: int) -> int:
    """How many bytes the body length prefix occupies on this header version.

    CORRECTED 2026-08-14 (CS-404). An earlier revision of this corpus wrote the
    int64 prefix on headers 13 and 14 and NO PREFIX AT ALL on header 10. That
    was wrong, and it was wrong in the direction that is hardest to notice: a
    parser written against it reads the object count where a real header-10 save
    carries a length, and every synthetic test still passes.

    Measured on real bodies of all four save versions: headers 13 and 14 open
    with an int64 equal to the body length minus 8, and header 10 opens with an
    int32 equal to the body length minus 4. Both are the length of the ENTIRE
    concatenated body across every chunk, excluding the prefix itself.

    Args:
        header_version: 10, 13 or 14.

    Returns:
        8 on headers 13 and 14, 4 on header 10.
    """
    if header_version >= HEADER_VERSION_WITH_BODY_LENGTH:
        return BODY_PREFIX_WIDTH_WIDE
    return BODY_PREFIX_WIDTH_NARROW


def body_with_prefix(body: bytes, header_version: int) -> bytes:
    """Prepend the version-appropriate body length prefix.

    One function so the two assembly sites cannot drift apart. The prefix
    follows the HEADER version; the transform delta follows the SAVE version.

    Args:
        body: The object section.
        header_version: 10, 13 or 14.

    Returns:
        The prefixed body.
    """
    if body_prefix_width(header_version) == BODY_PREFIX_WIDTH_WIDE:
        return _i64(len(body)) + body
    return _i32(len(body)) + body


def default_framing(header_version: int) -> str:
    """The framing a header version ships with.

    Args:
        header_version: 10, 13 or 14.

    Returns:
        The framing name.
    """
    if header_version >= HEADER_VERSION_WITH_TAIL:
        return FRAMING_MARKER22_ALGO
    return FRAMING_ZERO_MARKER_NOALGO


@dataclass(frozen=True)
class SyntheticSave:
    """A whole synthetic save, with the metadata a test needs to avoid restating it.

    ``chunk_offset`` is carried rather than rediscovered. A corruption helper
    that SEARCHED for the magic would be a small parser, and a small parser in
    a fixture is the thing this slice exists to avoid depending on.
    """

    name: str
    header_version: int
    save_version: int
    framing: str
    objects: tuple[SyntheticObject, ...]
    blob: bytes = field(repr=False)
    chunk_offset: int
    body: bytes = field(repr=False, default=b"")
    #: How many chunks the body was framed as. One for every fixture except
    #: SAVE_MULTICHUNK, which is the only one shaped like a real file.
    chunk_count: int = 1


def _int_kwarg(kwargs: dict[str, object], key: str, default: int) -> int:
    """Read an int out of a loosely typed kwargs dict, failing loudly on a wrong type.

    ``header_kwargs`` is ``dict[str, object]`` because it forwards every header
    field, so the two values this module has to READ back - the versions that
    drive framing and delta - need narrowing. A bare ``int(...)`` would accept a
    string and silently produce a fixture built at the wrong version, which is
    the one class of mistake this corpus must not be able to make quietly.

    Args:
        kwargs: The forwarded header kwargs.
        key: The field to read.
        default: Used when the field is absent.

    Returns:
        The value.

    Raises:
        TypeError: The value is present but is not an int.
    """
    value = kwargs.get(key, default)
    if not isinstance(value, int):
        raise TypeError(f"{key} must be an int, got {type(value).__name__}")
    return value


def build_save(
    *,
    header_kwargs: dict[str, object] | None = None,
    objects: tuple[SyntheticObject, ...] = (),
    framing: str | None = None,
) -> bytes:
    """Build a whole save: header, then one or more framed chunks.

    Args:
        header_kwargs: Passed straight to :func:`build_header`.
        objects: The body's records.
        framing: Defaults to the framing the header version ships with.

    Returns:
        The whole blob.
    """
    kwargs = dict(header_kwargs or {})
    header_version = _int_kwarg(kwargs, "header_version", HEADER_VERSION_14)
    save_version = _int_kwarg(kwargs, "save_version", 60)
    header = build_header(**kwargs)  # type: ignore[arg-type]
    body = build_body(objects, save_version=save_version)
    payload = body_with_prefix(body, header_version)
    return header + build_chunks(payload, framing=framing or default_framing(header_version))


def _assemble(
    name: str,
    *,
    header_version: int,
    save_version: int,
    objects: tuple[SyntheticObject, ...],
    framing: str | None = None,
    world_token: str = SYNTHETIC_WORLD_TOKEN,
    extra_header: dict[str, object] | None = None,
    max_chunk_size: int = MAX_CHUNK_SIZE,
) -> SyntheticSave:
    """Assemble one fixture and record where its first chunk starts.

    Args:
        name: The fixture's own name, so a test can report it without a lookup.
        header_version: Drives string layout, tail and body length prefix.
        save_version: Drives the transform delta.
        objects: The body's records.
        framing: Defaults to the header version's framing.
        world_token: The invented identifier.
        extra_header: Further header overrides.
        max_chunk_size: Decompressed bytes per chunk.

    Returns:
        The assembled fixture.
    """
    header_kwargs: dict[str, object] = {
        "header_version": header_version,
        "save_version": save_version,
        "world_token": world_token,
    }
    header_kwargs.update(extra_header or {})
    header = build_header(**header_kwargs)  # type: ignore[arg-type]
    chosen = framing or default_framing(header_version)
    body = build_body(objects, save_version=save_version)
    payload = body_with_prefix(body, header_version)
    parts = split_payload(payload, max_chunk_size)
    blob = header + build_chunks(payload, framing=chosen, max_chunk_size=max_chunk_size)
    return SyntheticSave(
        name=name,
        header_version=header_version,
        save_version=save_version,
        framing=chosen,
        objects=objects,
        blob=blob,
        chunk_offset=len(header),
        body=body,
        chunk_count=len(parts),
    )


_OBJECTS: Final = (
    SyntheticObject(
        "/Synthetic/Parts/Build_SyntheticSmelter.Build_SyntheticSmelter_C",
        "Persistent_Level:PersistentLevel",
        "SyntheticSmelter_0",
    ),
    SyntheticObject(
        "/Synthetic/Parts/Build_SyntheticBelt.Build_SyntheticBelt_C",
        "Persistent_Level:PersistentLevel",
        "SyntheticBelt_0",
        translation=(0.25, 64.0, 32.0),
    ),
)

#: Header 10, save 36, zero-marker framing, transform delta +4.
SAVE_V36: Final = _assemble("SAVE_V36", header_version=10, save_version=36, objects=_OBJECTS)

#: Header 13, save 42. Its object section is EMPTY because save version 42's
#: transform delta is UNMEASURED - see TRANSFORM_DELTA_BY_SAVE_VERSION.
SAVE_V42: Final = _assemble("SAVE_V42", header_version=13, save_version=42, objects=())

#: Header 14, save 52, transform delta +8.
SAVE_V52: Final = _assemble("SAVE_V52", header_version=14, save_version=52, objects=_OBJECTS)

#: Header 14, save 60, transform delta +8.
SAVE_V60: Final = _assemble("SAVE_V60", header_version=14, save_version=60, objects=_OBJECTS)

#: THE SHARPEST FIXTURE IN THE PHASE. Header 14 with save 36 occurs in NO real
#: file. It asserts that the STRING LAYOUT follows the HEADER version (four
#: strings, 28-byte tail, int64 body length) while the TRANSFORM OFFSET follows
#: the SAVE version (delta 4, not 8). A parser keying both decisions off a
#: single field passes every other fixture here and fails only this one.
SAVE_CROSS: Final = _assemble(
    "SAVE_CROSS",
    header_version=14,
    save_version=36,
    objects=_OBJECTS,
    world_token=SYNTHETIC_WORLD_TOKEN_B,
)

#: The five fixtures the phase was dispatched with. SAVE_MULTICHUNK below is
#: deliberately NOT in this tuple - the dispatched matrix is a stated contract
#: and a slice does not quietly widen one.
ALL_SAVES: Final = (SAVE_V36, SAVE_V42, SAVE_V52, SAVE_V60, SAVE_CROSS)


#: Enough records to push the body past two chunk boundaries at the REAL
#: 131072-byte split. Pinned rather than computed so the fixture's shape cannot
#: drift when the record layout changes; the test asserts the chunk count.
MULTICHUNK_OBJECT_COUNT: Final = 1600


def _multichunk_objects() -> tuple[SyntheticObject, ...]:
    """Build a body large enough to span several chunks.

    The records are near-identical on purpose. zlib collapses them to a few
    kilobytes, so the fixture is a genuine multi-chunk save whose DECOMPRESSED
    body exceeds 262144 bytes while the blob itself stays small enough to build
    at import.

    Returns:
        The records.
    """
    return tuple(
        SyntheticObject(
            "/Synthetic/Parts/Build_SyntheticSpan.Build_SyntheticSpan_C",
            "Persistent_Level:PersistentLevel",
            f"SyntheticSpan_{index}",
        )
        for index in range(MULTICHUNK_OBJECT_COUNT)
    )


#: THE FIXTURE THE BRIEF DID NOT ASK FOR AND THE REAL SAVE DEMANDED.
#:
#: The real save measured for this slice carries 13 chunks. Every other fixture
#: here is single-chunk, and in a single-chunk save the int64 body prefix equals
#: this chunk's payload minus 8 - so a chunk walker that reads exactly one chunk
#: and stops passes the entire rest of this corpus, then silently reports a
#: truncated world on every real file.
#:
#: It is split at the REAL 131072 boundary rather than an artificially small one,
#: so the max-chunk-size field it declares is the value a real file declares.
SAVE_MULTICHUNK: Final = _assemble(
    "SAVE_MULTICHUNK",
    header_version=14,
    save_version=60,
    objects=_multichunk_objects(),
)


def _assemble_levelled(
    name: str,
    *,
    header_version: int,
    save_version: int,
    named: tuple[SyntheticLevel, ...],
    persistent: SyntheticLevel,
    grids: tuple[SyntheticGrid, ...] = (),
) -> SyntheticSave:
    """Assemble a fixture whose body uses the MEASURED levelled layout.

    Separate from :func:`_assemble` rather than a flag on it. Every fixture
    already built by that function is asserted on by tests that exist, and a
    body-layout switch threaded through it would put those assertions one
    default value away from silently testing a different shape.

    Args:
        name: The fixture's own name.
        header_version: Drives string layout, tail and body length prefix.
        save_version: With the header version, selects the body layout.
        named: The named levels.
        persistent: The trailing unnamed level.
        grids: The grid preamble's grids, where the layout carries one.

    Returns:
        The assembled fixture.
    """
    header = build_header(header_version=header_version, save_version=save_version)
    body = build_levelled_body(
        named,
        persistent,
        header_version=header_version,
        save_version=save_version,
        grids=grids,
    )
    payload = body_with_prefix(body, header_version)
    framing = default_framing(header_version)
    return SyntheticSave(
        name=name,
        header_version=header_version,
        save_version=save_version,
        framing=framing,
        objects=tuple(obj for level in (*named, persistent) for obj in level.objects),
        blob=header + build_chunks(payload, framing=framing),
        chunk_offset=len(header),
        body=body,
        chunk_count=len(split_payload(payload)),
    )


#: The named levels of the levelled fixture. Deliberately UNEVEN: an empty
#: level, a level with actors only, and a level mixing actors with a component.
#: A uniform corpus would let a walker that mishandles an empty table, or that
#: reads the actor grammar for a component, pass anyway - and both are real
#: shapes in the measured body, where 165 of 201 named levels carry exactly one
#: record and one carries 14935.
LEVELLED_NAMED: Final = (
    SyntheticLevel(name="Persistent_Level:SyntheticGridCell_0"),
    SyntheticLevel(name="Persistent_Level:SyntheticGridCell_1", objects=_OBJECTS),
    SyntheticLevel(
        name="Persistent_Level:SyntheticGridCell_2",
        objects=(_OBJECTS[0],),
        components=(
            SyntheticComponent(
                "/Synthetic/Parts/Build_SyntheticInput.Build_SyntheticInput_C",
                "Persistent_Level:PersistentLevel",
                "SyntheticInput_0",
            ),
        ),
        collectables=(SyntheticCollectable(),),
    ),
)

#: The trailing unnamed level, which every measured body carries exactly once.
LEVELLED_PERSISTENT: Final = SyntheticLevel(
    name=None,
    objects=_OBJECTS,
    second_collectables=(SyntheticCollectable(),),
)

#: THE FIRST FIXTURE IN THIS CORPUS SHAPED LIKE A BODY A REAL SAVE CONTAINS.
#: Header 10 with save 36 - the first pair whose whole-body layout was measured.
SAVE_LEVELLED_V36: Final = _assemble_levelled(
    "SAVE_LEVELLED_V36",
    header_version=10,
    save_version=36,
    named=LEVELLED_NAMED,
    persistent=LEVELLED_PERSISTENT,
)

#: The named levels for the two pairs whose header collectable block is
#: OPTIONAL. The middle level carries NO block at all - its header section ends
#: at the record table - and that is the shape the size-driven rule exists for.
#:
#: It is a real shape, not a constructed one: 1943 of 2244 levels on the one
#: real (13,42) body have no block, and 1641 of 2945 on the (14,52) corpus. The
#: two rigid alternatives were run against the real files and both die - "always
#: read the block" stops at level 0, "never read it" stops at level 64 - so the
#: optionality is imposed by the format rather than chosen.
LEVELLED_NAMED_OPTIONAL_BLOCK: Final = (
    SyntheticLevel(name="Persistent_Level:SyntheticGridCell_0"),
    SyntheticLevel(
        name="Persistent_Level:SyntheticGridCell_1",
        objects=_OBJECTS,
        collectables=None,
    ),
    SyntheticLevel(
        name="Persistent_Level:SyntheticGridCell_2",
        objects=(_OBJECTS[0],),
        components=(
            SyntheticComponent(
                "/Synthetic/Parts/Build_SyntheticInput.Build_SyntheticInput_C",
                "Persistent_Level:PersistentLevel",
                "SyntheticInput_0",
            ),
        ),
        collectables=(SyntheticCollectable(),),
    ),
)

#: The grid preamble the three header-13 and header-14 pairs carry. Uneven on
#: purpose: an empty grid alongside a populated one, so a walker that mishandles
#: a zero cell count cannot pass.
LEVELLED_GRIDS: Final = (
    SyntheticGrid("SyntheticMainGrid"),
    SyntheticGrid(
        "SyntheticLandscapeGrid",
        cells=(
            SyntheticGridCell("SyntheticCell_x0_y0"),
            SyntheticGridCell("SyntheticCell_x1_y0"),
        ),
    ),
)

#: Header 13 with save 42. Transform delta 4, 8-byte section sizes, a grid
#: preamble, 12-byte data entries, save 36's four-string component and no level
#: tail. n=1 in the real library: one header-13 save exists on the machine this
#: was measured against, so every count behind this pair is a property of ONE
#: artifact until a second appears.
SAVE_LEVELLED_V42: Final = _assemble_levelled(
    "SAVE_LEVELLED_V42",
    header_version=13,
    save_version=42,
    named=LEVELLED_NAMED_OPTIONAL_BLOCK,
    persistent=LEVELLED_PERSISTENT,
    grids=LEVELLED_GRIDS,
)

#: Header 14 with save 52. Adds the component's 4-byte opaque pre-word and the
#: named level's closing int32 to the (13,42) shape, and moves the delta to 8.
SAVE_LEVELLED_V52: Final = _assemble_levelled(
    "SAVE_LEVELLED_V52",
    header_version=14,
    save_version=52,
    named=LEVELLED_NAMED_OPTIONAL_BLOCK,
    persistent=LEVELLED_PERSISTENT,
    grids=LEVELLED_GRIDS,
)

#: Header 14 with save 60, the most divergent pair. A package summary opens the
#: body and closes every named level, data entries carry a trailing int32, and
#: the second collectable block appears on the PERSISTENT LEVEL ONLY. Its named
#: levels all carry a header collectable block, matching the real files.
SAVE_LEVELLED_V60: Final = _assemble_levelled(
    "SAVE_LEVELLED_V60",
    header_version=14,
    save_version=60,
    named=LEVELLED_NAMED,
    persistent=LEVELLED_PERSISTENT,
    grids=LEVELLED_GRIDS,
)

#: Every levelled fixture, one per measured pair, in pair order.
LEVELLED_SAVES: Final = (
    SAVE_LEVELLED_V36,
    SAVE_LEVELLED_V42,
    SAVE_LEVELLED_V52,
    SAVE_LEVELLED_V60,
)

#: The named levels each levelled fixture was built from, so a test can derive
#: an expected record count instead of writing one down.
LEVELLED_NAMED_BY_PAIR: Final = {
    (10, 36): LEVELLED_NAMED,
    (13, 42): LEVELLED_NAMED_OPTIONAL_BLOCK,
    (14, 52): LEVELLED_NAMED_OPTIONAL_BLOCK,
    (14, 60): LEVELLED_NAMED,
}


# ---------------------------------------------------------------------------
# Truncation
# ---------------------------------------------------------------------------

SCOPE_FILE: Final = "file"
SCOPE_BODY: Final = "body"


@dataclass(frozen=True)
class TruncationPoint:
    """One named place to cut a blob in half.

    ``scope`` matters: a file-scope offset indexes the whole ``.sav``, while a
    body-scope offset indexes the DECOMPRESSED body. An object record lives
    inside the compressed stream, so "one byte short of a complete record"
    cannot be expressed as a file offset at all - cutting the compressed bytes
    there corrupts the inflate instead, which is a different case that
    ``mid-zlib-stream`` already covers.
    """

    label: str
    scope: str
    offset: int


def truncated_at(blob: bytes, n: int) -> bytes:
    """Cut a blob to its first ``n`` bytes.

    Args:
        blob: The source.
        n: The new length.

    Returns:
        The truncated blob.
    """
    return blob[:n]


def save_with_truncated_body(save: SyntheticSave, n: int) -> bytes:
    """Rebuild a save whose DECOMPRESSED body is cut to ``n`` bytes.

    The length prefix is rewritten to the truncated length and the stream is
    recompressed, so the file is well formed all the way down to the record
    walk. That is the point: the damage has to be reachable only after a
    successful inflate, or it is testing the framing again instead of the
    record walk.

    Args:
        save: The fixture to rebuild.
        n: The truncated body length.

    Returns:
        The whole blob.
    """
    payload = _i64(n) + save.body[:n]
    return save.blob[: save.chunk_offset] + build_chunk(payload, framing=save.framing)


#: Pinned cut points, all against SAVE_V60 except the body-scope one, which
#: indexes SAVE_V60's decompressed body. Each is asserted to land mid-structure
#: by the test module rather than merely declared to.
TRUNCATION_BOUNDARIES: Final = (
    # Inside the int32 count of the first string. Header 14 puts the save name
    # at offset 12, so 14 is two bytes into its length prefix.
    TruncationPoint("mid-length-prefix", SCOPE_FILE, 14),
    # Two bytes into that same string's payload.
    TruncationPoint("mid-string-bytes", SCOPE_FILE, 18),
    # Two bytes into the chunk magic.
    TruncationPoint("mid-magic", SCOPE_FILE, SAVE_V60.chunk_offset + 2),
    # Inside the first duplicated size, which starts at magic+17.
    TruncationPoint("mid-chunk-header", SCOPE_FILE, SAVE_V60.chunk_offset + 20),
    # Four bytes into the zlib stream.
    TruncationPoint(
        "mid-zlib-stream", SCOPE_FILE, SAVE_V60.chunk_offset + ZLIB_OFFSET_WITH_ALGO + 4
    ),
    # One byte short of the final object record's last field.
    TruncationPoint("one-byte-short-of-an-object-record", SCOPE_BODY, len(SAVE_V60.body) - 1),
)


# ---------------------------------------------------------------------------
# Named corruption cases
# ---------------------------------------------------------------------------

#: Neither measured marker, so a parser that accepts it is accepting anything.
CORRUPT_MARKER_VALUE: Final = 0xDEADBEEF
CORRUPT_MAGIC_VALUE: Final = 0x11223344

ABSURD_STRING_LENGTH: Final = 2**30
NEGATIVE_STRING_LENGTH: Final = -(2**30)

#: A terabyte declared by a chunk carrying a few hundred bytes. A parser that
#: preallocates on the declared size dies here rather than in production.
CHUNK_BOMB_UNCOMPRESSED_SIZE: Final = 1 << 40


def _splice(blob: bytes, offset: int, replacement: bytes) -> bytes:
    """Overwrite bytes in place without changing the length.

    Args:
        blob: The source.
        offset: Where to write.
        replacement: The new bytes.

    Returns:
        The spliced blob.
    """
    return blob[:offset] + replacement + blob[offset + len(replacement) :]


def corrupt_magic(save: SyntheticSave) -> bytes:
    """Replace the chunk magic, leaving every other byte intact.

    Args:
        save: The fixture to damage.

    Returns:
        The damaged blob.
    """
    return _splice(save.blob, save.chunk_offset, _u32(CORRUPT_MAGIC_VALUE))


def corrupt_marker(save: SyntheticSave) -> bytes:
    """Replace the marker with a value that is neither measured marker.

    Args:
        save: The fixture to damage.

    Returns:
        The damaged blob.
    """
    return _splice(save.blob, save.chunk_offset + 4, _u32(CORRUPT_MARKER_VALUE))


def corrupt_size_disagreement(save: SyntheticSave) -> bytes:
    """Make the duplicated compressed size disagree with its own copy.

    The duplication is the format's own checksum. A parser reading only the
    first copy cannot notice, and nothing else in the frame would tell it.

    Args:
        save: The fixture to damage.

    Returns:
        The damaged blob.
    """
    at = save.chunk_offset + sizes_offset(save.framing)
    (first,) = struct.unpack_from("<q", save.blob, at)
    return _splice(save.blob, at + 16, _i64(first + 1))


def corrupt_zlib_stream(save: SyntheticSave) -> bytes:
    """Damage the compressed stream while leaving the frame well formed.

    The frame must survive, or the case degenerates into the framing tests. The
    damage is placed past the two-byte zlib header so the stream still LOOKS
    like zlib and fails on the inflate rather than on the header check.

    Args:
        save: The fixture to damage.

    Returns:
        The damaged blob.
    """
    at = save.chunk_offset + ZLIB_OFFSET_WITH_ALGO + 6
    if save.framing == FRAMING_ZERO_MARKER_NOALGO:
        at = save.chunk_offset + ZLIB_OFFSET_WITHOUT_ALGO + 6
    original = save.blob[at]
    return _splice(save.blob, at, bytes([original ^ 0xFF]))


def absurd_string_length() -> bytes:
    """A header whose first string declares 2**30 bytes it does not carry.

    Returns:
        The damaged blob.
    """
    return _splice(SAVE_V60.blob, 12, _i32(ABSURD_STRING_LENGTH))


def negative_string_length() -> bytes:
    """A header whose first string declares -2**30 characters on the UTF-16 path.

    The negative sign selects UTF-16-LE, so a parser multiplies the magnitude
    by two before reading - which is why this case is not merely the previous
    one with a sign flipped.

    Returns:
        The damaged blob.
    """
    return _splice(SAVE_V60.blob, 12, _i32(NEGATIVE_STRING_LENGTH))


def declared_chunk_bomb(save: SyntheticSave) -> bytes:
    """Declare an uncompressed size far above any sane bound, in BOTH copies.

    Both copies are set, so the format's own consistency check still passes and
    a parser cannot dodge this case by noticing a size disagreement instead.

    Args:
        save: The fixture to damage.

    Returns:
        The damaged blob.
    """
    at = save.chunk_offset + sizes_offset(save.framing)
    blob = _splice(save.blob, at + 8, _i64(CHUNK_BOMB_UNCOMPRESSED_SIZE))
    return _splice(blob, at + 24, _i64(CHUNK_BOMB_UNCOMPRESSED_SIZE))


def unsupported_header_version() -> bytes:
    """A structurally well-formed save declaring header version 99.

    Built through :func:`build_save` with the two layout switches forced to the
    header-14 shape, so the only thing wrong with it is the declared version.
    A parser must reject it on the version rather than on a parse failure.

    Returns:
        The blob.
    """
    return build_save(
        header_kwargs={
            "header_version": UNSUPPORTED_HEADER_VERSION,
            "save_version": 60,
            "with_save_name": True,
            "with_tail": True,
        },
        objects=_OBJECTS,
    )


def unknown_actor_class() -> SyntheticSave:
    """A save carrying one actor whose class the registry does not model.

    Non-negotiable 7: unknown content is flagged and skipped, never fatal. So
    the record is STRUCTURALLY VALID and parses cleanly - the unknown-ness is in
    the class path alone. A fixture that made the bytes malformed too would let
    a parser reject it for the wrong reason and still look correct.

    Returns:
        The fixture.
    """
    objects = (
        _OBJECTS[0],
        SyntheticObject(
            UNKNOWN_ACTOR_CLASS_PATH,
            "Persistent_Level:PersistentLevel",
            "SyntheticUnknown_0",
        ),
    )
    return _assemble("UNKNOWN_ACTOR_CLASS", header_version=14, save_version=60, objects=objects)


# ---------------------------------------------------------------------------
# usmap
# ---------------------------------------------------------------------------

USMAP_MAGIC: Final = 0x30C4
USMAP_VERSION: Final = 0

USMAP_COMPRESSION_NONE: Final = 0
USMAP_COMPRESSION_OODLE: Final = 1
USMAP_COMPRESSION_BROTLI: Final = 2
USMAP_COMPRESSION_ZSTD: Final = 3

#: The file version at which the header gains a versioning block. MEASURED
#: 2026-08-15 (CS-404): the shipped file declares exactly this version.
USMAP_VERSION_VERSIONING: Final = 1

#: Bytes per custom version record - a 16-byte GUID and an int32. MEASURED: on
#: the shipped file the count sits at byte 15 and the next field at byte 1799,
#: which is 89 records of 20 bytes and nothing left over.
USMAP_CUSTOM_VERSION_BYTES: Final = 20

#: A schema super index with every bit set means "no super type". MEASURED:
#: 3900 of the shipped file's schemas carry it.
USMAP_NO_SUPER: Final = 0xFFFFFFFF

#: The three versioning-block integers a reader SKIPS rather than interprets,
#: plus the filler byte for the custom version records it also skips.
#:
#: Every SKIPPED byte is NON-ZERO on purpose - the two engine versions, the
#: records and the changelist. The bHasVersioning flag and the record count are
#: meaningful small integers and carry zero bytes, necessarily.
#:
#: The reason is mechanical rather than decorative. The compression method is
#: the byte immediately after this block.
#: A reader whose skip arithmetic is wrong lands inside the block and reads its
#: method byte from here - and method 0 is the ONE value that parses. Zero
#: filler would therefore turn a misaligned skip into a silent success with
#: garbage sizes; non-zero filler turns it into a clean
#: UnsupportedUsmapCompressionError naming a nonsense method.
#:
#: CORRECTED 2026-08-15: the records were zero-filled while this note claimed
#: the block was not, so the stated rationale held for 12 of the block's bytes
#: and failed for the 20N bytes that dominate it. A mutation filling them with
#: 0xFF changed nothing any test could see.
#: ``test_every_byte_of_the_versioning_block_is_non_zero`` is the check.
_USMAP_FILE_VERSION_UE4: Final = 0x5C5C5C5C
_USMAP_FILE_VERSION_UE5: Final = 0x5D5D5D5D
_USMAP_NETWORK_CHANGELIST: Final = 0x5E5E5E5E
_USMAP_CUSTOM_VERSION_FILL: Final = 0x5F

#: What each property type writes AFTER its type byte, as
#: ``(inner descriptor count, trailing name index)``.
#:
#: MEASURED 2026-08-15 (CS-404) from the shipped file, and measured in the only
#: way that settles it: walking the real name, enum and schema sections with
#: this table lands EXACTLY on the four-character ASCII tag that opens the
#: trailing extension container, with every name index in bounds and every type
#: byte at or below 29. Dropping ANY row below, or swapping ANY row's shape for
#: any of the other three, desynchronises the walk before it reaches the tag -
#: all 20 perturbations were run and all 20 broke. A table that is wrong
#: somewhere does not land on a tag boundary by accident.
#:
#: This is a MEASUREMENT OF THE FORMAT, not of a fixture. That distinction is
#: the whole point of CS-404: the previous inner grammar here was a
#: self-consistent placeholder, so every usmap fixture in the corpus agreed
#: with the builder and with nothing else.
USMAP_PROPERTY_PAYLOAD: Final[Mapping[int, tuple[int, bool]]] = MappingProxyType(
    {
        8: (1, False),  # array: one inner descriptor
        9: (0, True),  # struct: one name-table index
        24: (2, False),  # map: a key descriptor then a value descriptor
        25: (1, False),  # set: one inner descriptor
        26: (1, True),  # enum: an inner descriptor then the enum name
    }
)


# --- how each fact about the shipped grammar is known, AS DATA ---------------
#
# CS-412 discipline. "Measured" is not one thing, and collapsing four different
# strengths of evidence into that one word is how a later reader promotes a
# coincidence into a constraint. The landing oracle - walk the real sections and
# arrive exactly on the trailing tag - is decisive for MOST fields and settles
# NOTHING for others, and prose cannot be queried for which is which.
#
# The strengths, weakest last:
#
#   REBUILD         this builder re-emits the real file's own bytes for every
#                   entity of this kind. The strongest available: it cannot be
#                   satisfied by a self-consistent wrong answer.
#   LANDING         a walk using this fact consumes the sections and lands
#                   exactly on the trailing tag; perturbing it does not.
#   DISTRIBUTION    the landing does NOT discriminate this. It is settled by
#                   what the values look like across the whole file.
#   UNCONTRADICTED  observed range on ONE file of ONE build. Not a constraint -
#                   a ceiling nothing has yet exceeded.
#   SYNTHETIC_ONLY  not present in the shipped file at all. The builder can
#                   emit it; the format may or may not permit it.

USMAP_BASIS_REBUILD: Final = "rebuild"
USMAP_BASIS_LANDING: Final = "landing"
USMAP_BASIS_DISTRIBUTION: Final = "distribution"
USMAP_BASIS_UNCONTRADICTED: Final = "uncontradicted"
USMAP_BASIS_SYNTHETIC_ONLY: Final = "synthetic-only"

USMAP_BASES: Final = (
    USMAP_BASIS_REBUILD,
    USMAP_BASIS_LANDING,
    USMAP_BASIS_DISTRIBUTION,
    USMAP_BASIS_UNCONTRADICTED,
    USMAP_BASIS_SYNTHETIC_ONLY,
)


@dataclass(frozen=True)
class UsmapEvidence:
    """How ONE fact about the shipped usmap grammar is known.

    Attributes:
        subject: The field or property the claim is about.
        basis: One of :data:`USMAP_BASES`.
        detail: The measurement, including the number that supports it.
    """

    subject: str
    basis: str
    detail: str


#: Measured 2026-08-15 (CS-404) against one file of the pinned build. Every
#: number below was observed, not carried forward from a document.
USMAP_EVIDENCE: Final[tuple[UsmapEvidence, ...]] = (
    UsmapEvidence(
        "enum section encoding",
        USMAP_BASIS_REBUILD,
        "all 2603 real enums re-emit byte-identically from this builder",
    ),
    UsmapEvidence(
        "schema section encoding",
        USMAP_BASIS_REBUILD,
        "13697 of 13792 real schemas re-emit byte-identically; the 95 "
        "exceptions are exactly those with property_count != serializable "
        "count, which this builder cannot express - see UsmapSchema",
    ),
    UsmapEvidence(
        "type-26 field order (inner descriptor BEFORE the name index)",
        USMAP_BASIS_REBUILD,
        "NOT settled by landing: writing the name first consumes identical "
        "bytes and lands on the same tag at 1896914. It is settled by the "
        "rebuild, and separately by in-bounds validation - name-first puts a "
        "type-26 name index outside the 57985-entry table on the real file. "
        "3113 such descriptors across 1873 schemas, nesting included",
    ),
    UsmapEvidence(
        "name/enum/schema counts and widths, payload shapes",
        USMAP_BASIS_LANDING,
        "38 single-field perturbations were run across two sessions and all 38 "
        "fail to land on the trailing tag; the unperturbed walk consumes "
        "1896914 with 784830 trailing",
    ),
    UsmapEvidence(
        "entry field ORDER: slot before array_size",
        USMAP_BASIS_DISTRIBUTION,
        "landing does NOT discriminate this - swapping the two lands "
        "byte-identically at 1896914. Settled only by value distribution: slot "
        "equals the loop index in 9725 of 9795 non-empty schemas, and "
        "array_size is 1 in 48075 of 48223 entries",
    ),
    UsmapEvidence(
        "MAX_KNOWN_PROPERTY_TYPE = 29",
        USMAP_BASIS_UNCONTRADICTED,
        "the observed maximum, NOT a constraint - raising a walker's ceiling "
        "to 255 lands identically. Type ids 0-15 and 17-29 occur; 16 does not",
    ),
    UsmapEvidence(
        "value ceilings",
        USMAP_BASIS_UNCONTRADICTED,
        "one file of one build: name length max 73, enum member count max 114, "
        "array_size max 61, property_count max 493, slot max 492, descriptor "
        "nesting depth max 2",
    ),
    UsmapEvidence(
        "bHasVersioning == 0",
        USMAP_BASIS_SYNTHETIC_ONLY,
        "the shipped file declares 1 with 89 custom version records; the "
        "zero branch is reachable only from build_usmap(custom_versions=None)",
    ),
    UsmapEvidence(
        "compression methods other than 0",
        USMAP_BASIS_SYNTHETIC_ONLY,
        "the shipped file is uncompressed; 1, 2 and 3 are declared by "
        "usmap_with_compression over an uncompressed body so a loader can be "
        "tested for refusing them",
    ),
    UsmapEvidence(
        "descriptor nesting deeper than 2",
        USMAP_BASIS_SYNTHETIC_ONLY,
        "the real file nests at most 2 deep; deeper trees are builder-only",
    ),
)


@dataclass(frozen=True)
class UsmapType:
    """One property-type descriptor for :func:`build_usmap`'s shipped mode.

    Attributes:
        type_id: The raw type byte.
        name: The trailing name-table index's name, for the types that carry
            one - struct and enum. Must appear in the name table.
        inner: Nested descriptors, for the types that carry them - one for an
            array, a set or an enum, and two for a map (key then value).
        array_size: The declared fixed-array width. 1 is a scalar.
    """

    type_id: int
    name: str | None = None
    inner: tuple[UsmapType, ...] = ()
    array_size: int = 1


@dataclass(frozen=True)
class UsmapSchema:
    """One schema for :func:`build_usmap`'s shipped-grammar mode.

    TWO REAL SHAPES THIS STRUCTURALLY CANNOT EMIT, stated here rather than
    discovered later. Both are the same 95 schemas of the shipped file's 13792:

    - ``property_count != serializable_count``. This writes the two counts
      equal, because it has one property list. 95 real schemas declare more
      properties than they serialize.
    - NON-SEQUENTIAL SLOTS. This writes ``slot`` as the loop index. 70 real
      schemas number their slots with gaps - and all 70 are inside those same
      95, so the two gaps are one gap, not two.

    Nothing above this layer reads either field in a way that cares yet, and
    inventing a second knob before a caller needs it would be modelling rather
    than measuring. ``test_the_builder_reproduces_the_shipped_bytes_it_models``
    asserts the shortfall is EXACTLY those schemas and nothing else, so this
    stops being an unbounded claim and becomes a counted one.

    Attributes:
        name: The schema name. Must appear in the name table.
        super_name: The super type's name, or None for no super, which is
            written as :data:`USMAP_NO_SUPER`.
        properties: ``(property name, type)`` in slot order. The type is either
            a bare type id, which is only valid for a type that carries no
            payload, or a :class:`UsmapType`.
    """

    name: str
    super_name: str | None = None
    properties: tuple[tuple[str, int | UsmapType], ...] = ()


#: What may be handed to ``build_usmap(schemas=...)``. The tuple form is the
#: legacy grammar's and the dataclass is the shipped grammar's; mixing a form
#: with the wrong mode is refused rather than guessed at.
UsmapSchemaSpec = tuple[str, Sequence[str]] | UsmapSchema


def _usmap_name(text: str) -> bytes:
    """Encode one name as a uint8 length and that many UTF-8 bytes.

    MEASURED: this is the name-table encoding in the shipped file, and it is
    the one section the legacy and shipped grammars agree on. A uint16 length
    runs the walk off the end of the real file.
    """
    raw = text.encode("utf-8")
    return struct.pack("<B", len(raw)) + raw


def _usmap_index(table: Mapping[str, int], text: str) -> bytes:
    """Pack a uint32 name-table index, refusing a name the table lacks.

    THIS FUNCTION IS AN ECHO PATH AND CANNOT BE MADE OTHERWISE. Keeping ``text``
    out of the exception MESSAGE does not contain it: pytest renders the
    ARGUMENTS of every frame in a failing traceback with no ``--showlocals``,
    and ``text`` and ``table`` are arguments. Measured 2026-08-15 on this
    machine - a deliberately failing call printed ``text = '...'`` verbatim.
    ``test_a_failing_builder_call_renders_its_arguments`` pins that behaviour so
    a future pytest cannot quietly change it.

    An earlier revision of this docstring claimed the opposite, naming the exact
    mechanism and then asserting a mitigation that mechanism defeats. That is
    worse than saying nothing: non-negotiable 12 is about echo paths, and a
    documented mitigation that does not work invites the pattern being copied to
    a frame that carries real save bytes.

    WHAT ACTUALLY MAKES THIS SAFE is the input, not the code: every caller in
    the corpus passes invented names. A caller handing REAL names to this
    builder - the shipped-file rebuild audit in ``tests/save/test_usmap.py`` is
    the only one - owns containing its own exceptions before they reach pytest,
    and that one does, reporting counts and an exception TYPE and nothing else.
    """
    position = table.get(text)
    if position is None:
        raise ValueError(
            "shipped-grammar mode writes every enum, schema and property name "
            "as a uint32 index, so each one must appear in the name table"
        )
    return _u32(position)


def _usmap_descriptor(spec: int | UsmapType, table: Mapping[str, int]) -> bytes:
    """Write one property-type byte and its payload.

    Refusing an under-specified descriptor is the point rather than a
    convenience. A builder that wrote the type byte and omitted the payload
    would emit a fixture whose next entry is read from the wrong offset - which
    is precisely the silently-wrong corpus CS-404 exists to remove, and no
    assertion written against such a corpus could see it.

    Args:
        spec: A bare type id, or a :class:`UsmapType`.
        table: Name to name-table index.

    Returns:
        The type byte followed by its payload.

    Raises:
        ValueError: The descriptor does not carry what its type id requires.
    """
    descriptor = spec if isinstance(spec, UsmapType) else UsmapType(spec)
    inner_count, has_name = USMAP_PROPERTY_PAYLOAD.get(descriptor.type_id, (0, False))

    if len(descriptor.inner) != inner_count:
        raise ValueError(
            f"property type {descriptor.type_id} takes {inner_count} inner "
            f"descriptor(s) and was given {len(descriptor.inner)}; writing the "
            "type byte without its payload desynchronises the whole section"
        )
    if has_name and descriptor.name is None:
        raise ValueError(
            f"property type {descriptor.type_id} writes a name index after its "
            "inner descriptor, so UsmapType.name is required for it"
        )

    out = [struct.pack("<B", descriptor.type_id)]
    out.extend(_usmap_descriptor(child, table) for child in descriptor.inner)
    if has_name and descriptor.name is not None:
        out.append(_usmap_index(table, descriptor.name))
    return b"".join(out)


def usmap_name_table(names: Sequence[str]) -> Mapping[str, int]:
    """Build the name-to-index table the shipped grammar writes indices from.

    Public because the shipped-bytes rebuild audit needs to build it ONCE and
    reuse it across thousands of entries. Duplicate names resolve to the LAST
    position, which is a real difference from the file for a name table that
    repeats - the shipped file's 57985 names are all distinct, measured.

    Args:
        names: The name table, in file order.

    Returns:
        Name to index.
    """
    return {text: position for position, text in enumerate(names)}


def build_usmap_enum_entry(name: str, members: Sequence[str], table: Mapping[str, int]) -> bytes:
    """Write ONE enum in the shipped grammar, with no section count prefix.

    Args:
        name: The enum name. Must be in ``table``.
        members: The member names. Each must be in ``table``.
        table: From :func:`usmap_name_table`.

    Returns:
        The entry bytes.
    """
    out = [_usmap_index(table, name), struct.pack("<B", len(members))]
    out.extend(_usmap_index(table, member) for member in members)
    return b"".join(out)


def _usmap_enums(
    enums: Sequence[tuple[str, Sequence[str]]],
    table: Mapping[str, int],
    *,
    shipped: bool,
) -> bytes:
    """Write the enum section in whichever grammar was asked for."""
    out = [_u32(len(enums))]
    for enum_name, members in enums:
        if shipped:
            out.append(build_usmap_enum_entry(enum_name, members, table))
        else:
            out.append(_usmap_name(enum_name))
            out.append(struct.pack("<B", len(members)))
            out.extend(_usmap_name(member) for member in members)
    return b"".join(out)


def build_usmap_schema_entry(schema: UsmapSchema, table: Mapping[str, int]) -> bytes:
    """Write ONE schema in the shipped grammar, with no section count prefix.

    The property count and the serializable count are written equal, and the
    slot is written as the loop index. MEASURED: the two counts agree on 13697
    of the shipped file's 13792 schemas and the slots are sequential in all of
    those, so both shortfalls are the same 95 schemas - see
    :class:`UsmapSchema`. The entry loop is driven by the SERIALIZABLE count;
    walking on the property count instead desynchronises the real file.

    Public because the shipped-bytes rebuild audit compares its output against
    the game's own bytes, entry by entry.

    Args:
        schema: The schema to write.
        table: From :func:`usmap_name_table`.

    Returns:
        The entry bytes.
    """
    out = [
        _usmap_index(table, schema.name),
        _u32(USMAP_NO_SUPER)
        if schema.super_name is None
        else _usmap_index(table, schema.super_name),
        struct.pack("<H", len(schema.properties)),
        struct.pack("<H", len(schema.properties)),
    ]
    for slot, (property_name, spec) in enumerate(schema.properties):
        descriptor = spec if isinstance(spec, UsmapType) else UsmapType(spec)
        out.append(struct.pack("<H", slot))
        out.append(struct.pack("<B", descriptor.array_size))
        out.append(_usmap_index(table, property_name))
        out.append(_usmap_descriptor(descriptor, table))
    return b"".join(out)


def _usmap_schemas(
    schemas: Sequence[UsmapSchemaSpec],
    table: Mapping[str, int],
    *,
    shipped: bool,
) -> bytes:
    """Write the schema section in whichever grammar was asked for.

    Raises:
        ValueError: A schema was given in the form the other mode takes.
    """
    out = [_u32(len(schemas))]
    for entry in schemas:
        if shipped:
            if not isinstance(entry, UsmapSchema):
                raise ValueError(
                    "shipped-grammar mode needs a UsmapSchema per schema - a "
                    "(name, properties) tuple carries no super type and no "
                    "property type ids, and neither may be invented here"
                )
            out.append(build_usmap_schema_entry(entry, table))
        else:
            if isinstance(entry, UsmapSchema):
                raise ValueError(
                    "a UsmapSchema describes the shipped grammar; pass "
                    "shipped=True, or use a (name, properties) tuple"
                )
            schema_name, properties = entry
            out.append(_usmap_name(schema_name))
            out.append(struct.pack("<H", len(properties)))
            out.extend(_usmap_name(prop) for prop in properties)
    return b"".join(out)


def build_usmap_body(
    *,
    names: Sequence[str],
    enums: Sequence[tuple[str, Sequence[str]]],
    schemas: Sequence[UsmapSchemaSpec],
    shipped: bool = False,
) -> bytes:
    """Build a usmap BODY, with no outer framing.

    Exposed separately so a test can damage or extend the body - truncate a
    section, append a trailing extension block - and then reframe it, which is
    the only way to exercise a loader's in-body error paths without also
    tripping the container's own length check.

    Args:
        names: The name table.
        enums: ``(enum name, member names)`` pairs.
        schemas: See :data:`UsmapSchemaSpec`.
        shipped: Write the MEASURED shipped grammar for the enum and schema
            sections rather than the legacy placeholder. See :func:`build_usmap`.

    Returns:
        The body bytes.
    """
    table = usmap_name_table(names)
    out = [_u32(len(names))]
    out.extend(_usmap_name(text) for text in names)
    out.append(_usmap_enums(enums, table, shipped=shipped))
    out.append(_usmap_schemas(schemas, table, shipped=shipped))
    return b"".join(out)


def build_usmap(
    *,
    names: Sequence[str],
    enums: Sequence[tuple[str, Sequence[str]]],
    schemas: Sequence[UsmapSchemaSpec],
    compression_method: int = USMAP_COMPRESSION_NONE,
    version: int = USMAP_VERSION,
    custom_versions: int | None = None,
    shipped: bool = False,
) -> bytes:
    """Build a usmap.

    TWO INNER GRAMMARS, AND THE DIFFERENCE IS THE POINT.

    ``shipped=False`` is the ORIGINAL, MODELLED grammar: enum and schema names
    are written inline as uint8-length-prefixed strings and a property carries
    no type byte at all. It is a self-consistent placeholder and it is NOT the
    shipped format. It is kept, and is still the default, because fixtures
    across the corpus are built on it and moving them would put a large body of
    existing assertions on new bytes for no gain.

    ``shipped=True`` is the MEASURED grammar, derived from the shipped file for
    CS-404 and verified by round-tripping through the real loader:

      names    uint32 count, then a uint8 length and that many UTF-8 bytes
               each. The one section both grammars agree on.
      enums    uint32 count, then per enum a uint32 index into the name table,
               a uint8 member count, and that many uint32 indices.
      schemas  uint32 count, then per schema a uint32 name index, a uint32
               super index (:data:`USMAP_NO_SUPER` for none), a uint16 property
               count and a uint16 serializable count, then that many entries.
      entry    uint16 slot, uint8 array size, uint32 name index, uint8 type,
               then the payload in :data:`USMAP_PROPERTY_PAYLOAD`.

    WHY BOTH EXIST RATHER THAN ONE REPLACING THE OTHER: before CS-404 there was
    only the placeholder, so no fixture anywhere had ever driven the loader's
    real inner grammar, and every usmap test in the corpus could only agree
    with whoever wrote the builder. Deleting the placeholder would have been a
    second, larger change on top of closing that gap.

    THE OUTER FRAMING is measured: magic (uint16), version (uint8), then - from
    version 1 - a versioning block, then the compression method (uint8) and the
    compressed and decompressed sizes (uint32 each). The header size is
    therefore DERIVED by walking the fields, never assumed.

    The declared compression method is written verbatim even when the body is
    not actually compressed, and the declared custom version count is written
    verbatim even when it is out of range. Both are deliberate: a loader can
    only be tested for REJECTING a value if the declaration is free to lie.

    Args:
        names: The name table.
        enums: ``(enum name, member names)`` pairs.
        schemas: See :data:`UsmapSchemaSpec`.
        compression_method: Declared verbatim. 0 is none.
        version: The file version byte. The default writes no versioning block
            at all, which is what every pre-CS-404 call site got.
        custom_versions: Only consulted from version 1. None declares
            ``bHasVersioning`` 0 and writes nothing further; an int declares
            the flag set and that many custom version records. The count is
            declared verbatim, and that many records are written when it is
            positive.
        shipped: Write the measured shipped grammar. See above.

    Returns:
        The usmap bytes.
    """
    payload = build_usmap_body(names=names, enums=enums, schemas=schemas, shipped=shipped)

    head = [struct.pack("<H", USMAP_MAGIC), struct.pack("<B", version)]
    if version >= USMAP_VERSION_VERSIONING:
        if custom_versions is None:
            head.append(_i32(0))
        else:
            head.append(_i32(1))
            head.append(_i32(_USMAP_FILE_VERSION_UE4))
            head.append(_i32(_USMAP_FILE_VERSION_UE5))
            head.append(_i32(custom_versions))
            head.append(
                bytes(
                    [_USMAP_CUSTOM_VERSION_FILL]
                    * (max(custom_versions, 0) * USMAP_CUSTOM_VERSION_BYTES)
                )
            )
            head.append(_i32(_USMAP_NETWORK_CHANGELIST))
    head.append(struct.pack("<B", compression_method))
    head.append(_u32(len(payload)))
    head.append(_u32(len(payload)))
    return b"".join(head) + payload


def usmap_with_compression(method: int) -> bytes:
    """A usmap declaring a compression method, over an uncompressed body.

    Args:
        method: The declared method. 0 none, 1 Oodle, 2 Brotli, 3 Zstandard.

    Returns:
        The usmap bytes.
    """
    return build_usmap(
        names=["SyntheticName", "SyntheticProperty"],
        enums=[("ESyntheticEnum", ["Alpha", "Beta"])],
        schemas=[("SyntheticSchema", ["SyntheticProperty"])],
        compression_method=method,
    )
