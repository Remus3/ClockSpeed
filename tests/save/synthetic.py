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
- the int64 body length prefix on 13 and 14 and its absence on 10,
- the transform deltas for save versions 36, 52 and 60.

MODELLED - a self-consistent construction, NOT a measurement:

- the 28 tail bytes' internal structure (only the WIDTH is measured),
- the object record's own field layout (only the DELTA is measured),
- the order within the duplicated size pair,
- the empty-string encoding,
- the usmap inner grammar (only the outer 12-byte framing is modelled with
  any confidence).

Each is flagged again where it is built.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass, field
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

#: MEASURED. The byte delta before the transform block, by SAVE version.
#:
#: SAVE VERSION 42 IS DELIBERATELY ABSENT. Its delta was never measured, and 36
#: -> 4 with 52 -> 8 makes 4 or 6 look "obviously" right for 42. Interpolating
#: it would be inventing a measurement because it feels derived - the same
#: failure class as trusting a fixture built parallel to the code. SAVE_V42
#: therefore carries an EMPTY object section, and a later slice that measures
#: the real value owns adding it here.
TRANSFORM_DELTA_BY_SAVE_VERSION: Final = {36: 4, 52: 8, 60: 8}

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
    blob: bytes
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
    payload = _i64(len(body)) + body if header_version >= HEADER_VERSION_WITH_BODY_LENGTH else body
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
    payload = _i64(len(body)) + body if header_version >= HEADER_VERSION_WITH_BODY_LENGTH else body
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


def build_usmap(
    *,
    names: list[str] | tuple[str, ...],
    enums: list[tuple[str, list[str]]] | tuple[tuple[str, list[str]], ...],
    schemas: list[tuple[str, list[str]]] | tuple[tuple[str, list[str]], ...],
    compression_method: int = USMAP_COMPRESSION_NONE,
) -> bytes:
    """Build a usmap.

    MODELLED, not measured, EXCEPT the outer 12-byte framing: magic (uint16),
    version (uint8), compression method (uint8), compressed size (uint32),
    decompressed size (uint32). The INNER grammar below - counts and
    uint8-length-prefixed names - is a self-consistent placeholder. A slice that
    loads a real usmap owns replacing it, and must not read this as evidence.

    The declared compression method is written verbatim even when the body is
    not actually compressed. That is deliberate: :func:`usmap_with_compression`
    exists so a loader can be tested for REJECTING a method it cannot handle,
    and it can only do that if the declaration is free to lie.

    Args:
        names: The name table.
        enums: ``(enum name, member names)`` pairs.
        schemas: ``(schema name, property names)`` pairs.
        compression_method: Declared verbatim. 0 is none.

    Returns:
        The usmap bytes.
    """

    def _name(text: str) -> bytes:
        raw = text.encode("utf-8")
        return struct.pack("<B", len(raw)) + raw

    body = [_u32(len(names))]
    body.extend(_name(text) for text in names)
    body.append(_u32(len(enums)))
    for enum_name, members in enums:
        body.append(_name(enum_name))
        body.append(struct.pack("<B", len(members)))
        body.extend(_name(member) for member in members)
    body.append(_u32(len(schemas)))
    for schema_name, properties in schemas:
        body.append(_name(schema_name))
        body.append(struct.pack("<H", len(properties)))
        body.extend(_name(prop) for prop in properties)
    payload = b"".join(body)

    head = (
        struct.pack("<H", USMAP_MAGIC)
        + struct.pack("<B", USMAP_VERSION)
        + struct.pack("<B", compression_method)
        + _u32(len(payload))
        + _u32(len(payload))
    )
    return head + payload


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
