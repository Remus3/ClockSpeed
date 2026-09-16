"""The save header parse, across every measured header version.

WHAT THIS MODULE OWNS
-----------------------
The three leading version fields, the version-dispatched string block, the
fixed block, the world token, and ``body_offset`` - the absolute offset of the
chunk magic, which is the single seam this module hands to the chunk walker.

It does NOT validate the chunk frame. A header parser that decoded the marker
word or the compressed sizes would be reaching past its neighbour, which
BOOTSTRAP.md section 6 calls a design bug. The one thing this module asserts
about the body is that four bytes exist at ``body_offset``, because promising
an offset it has not confirmed is reachable would make the seam a guess.

THE LAYOUT IS VERSION DISPATCHED - see docs/adr/0007
------------------------------------------------------
BOOTSTRAP.md section 2.4 owns the measurement. In summary, and restated here
only as far as the code needs it:

- every version opens with int32 header version, int32 save version, int32
  build changelist;
- header 14 then carries FOUR length-prefixed strings and headers 10 and 13
  carry THREE, the extra one on 14 being a save name at the FRONT;
- the fixed block after the strings is identical on every version;
- headers 13 and 14 carry a 28-byte tail after the identifier and header 10
  carries none.

PRIVACY IS THE REASON THIS MODULE EXISTS, NOT A FEATURE OF IT
---------------------------------------------------------------
ADR 0007 records the mechanism precisely: a redactor aimed at a NAMED field is
defeated by a version-dependent field ORDER. On header versions 10 and 13 the
THIRD string is the operator's world name; on header version 14 the third
string is the options string. A probe leaked a world name by exactly that
off-by-one. Four consequences are built into the design here:

1. :class:`SaveHeader` carries NO field holding a save name, an options string
   or a session name. They are not redacted - they are ABSENT. Unreachable
   beats redacted.
2. The default parse never DECODES them either. It reads their declared length
   and steps over the bytes, so the values do not become Python strings at all
   and cannot appear in a local-variable dump.
3. Rendering them requires :func:`reveal_strings` with an explicit keyword-only
   opt-in. That path is RENDER-SITE ONLY: the result is never stored on a
   long-lived object, never logged, never placed in exception context. ADR 0007
   decision item 4 states why the friction is load-bearing -
   ``clockspeed.data.locate.redact()`` holds no needle for a session name read
   out of a header, because that string is not knowable in advance, so the one
   sanctioned accessor returns a string this project's own redactor CANNOT
   neutralize.
4. :class:`SaveHeader` uses ``repr=False`` with a hand-written ``__repr__``
   emitting versions and a MASKED token only. The generated repr prints every
   field, and a test runner reprs objects into the log.

THE ERROR TAXONOMY IS A CLOSED SURFACE, NOT A CONVENTION
----------------------------------------------------------
Every exception below takes structured keyword parameters drawn from a fixed
vocabulary: a field NAME from :data:`FIELD_NAMES`, a byte OFFSET, an
expected/actual LENGTH or COUNT, a version scalar, a fixed reason, an
already-redacted path, and an errno. There is no parameter through which raw
bytes, a decoded string or an unredacted path could travel, at any raise site,
including one written later. A decode failure is re-raised ``from None`` so the
original :class:`UnicodeDecodeError`, whose message quotes the offending bytes,
cannot arrive as exception context.

The string block is named POSITIONALLY in errors - ``header_string_0`` and so
on - rather than by field name. That is the same discipline ADR 0007 requires
of the redactor: the name is stable across versions and the position is not, so
an error that named a field could name the wrong one.

BOUND BEFORE ALLOCATING
-------------------------
A save is untrusted binary input. Every declared string length is checked
against :data:`MAX_STRING_BYTES` BEFORE the remaining length is consulted and
before any slice is taken, and :func:`read_header` reads at most
:data:`MAX_HEADER_BYTES`. Both caps sit far above every measured header.

INDEPENDENCE FROM THE FIXTURE BUILDER, DELIBERATELY
-----------------------------------------------------
This module imports nothing from the corpus the suite is written against, and
spells its own copy of every measured constant. Both are independent encodings
of the measurement BOOTSTRAP.md section 2.4 owns. Sharing the constants would
make the suite a restatement of this module's own opinion rather than a check
on it, which is the parallel-fixture failure class recorded in
``memory/test-quality-failure-classes.md``.
"""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Final

from clockspeed.data.locate import redact

# ---------------------------------------------------------------------------
# Measured layout constants - BOOTSTRAP.md section 2.4 owns the measurement
# ---------------------------------------------------------------------------

HEADER_VERSION_10: Final = 10
HEADER_VERSION_13: Final = 13
HEADER_VERSION_14: Final = 14

#: The versions this module has a MEASURED layout for. Anything else is
#: refused outright rather than parsed against the newest known shape, per ADR
#: 0007: extrapolating a layout from the newest version is the guess that
#: produces a plausible-looking wrong parse.
SUPPORTED_HEADER_VERSIONS: Final = (HEADER_VERSION_10, HEADER_VERSION_13, HEADER_VERSION_14)

#: Header 14 adds a save name at the FRONT of the string block.
HEADER_VERSION_WITH_SAVE_NAME: Final = HEADER_VERSION_14

#: Headers 13 and 14 carry a tail between the identifier and the chunk magic.
HEADER_VERSION_WITH_TAIL: Final = HEADER_VERSION_13

#: The tail is skipped BY LENGTH. Its internal structure is unverified and no
#: field breakdown is invented for it (ADR 0007 decision item 5).
HEADER_TAIL_SIZE: Final = 28

#: The measured identifier: 22 characters of base64url, 16 bytes decoded. A
#: different length is flagged and carried, never refused - non-negotiable 7.
WORLD_TOKEN_LENGTH: Final = 22

#: The (header version, save version) pairs present in the measured library.
#: A pair outside this set is flagged: the LAYOUT is still known, because it
#: follows the header version alone, but the combination is unattested and a
#: caller is owed that fact.
MEASURED_VERSION_PAIRS: Final = frozenset(
    {
        (HEADER_VERSION_10, 36),
        (HEADER_VERSION_13, 42),
        (HEADER_VERSION_14, 52),
        (HEADER_VERSION_14, 60),
    }
)

# --- widths ----------------------------------------------------------------

INT8_SIZE: Final = 1
INT32_SIZE: Final = 4
INT64_SIZE: Final = 8

#: A negative string count selects UTF-16-LE and its magnitude is a CHARACTER
#: count, so the byte count is twice it. A parser treating the magnitude as
#: bytes reads half the string and lands mid-field.
UTF16_CHAR_SIZE: Final = 2

#: The chunk magic this module confirms is reachable at ``body_offset``. Its
#: VALUE is the chunk walker's business; only its width is needed here.
CHUNK_MAGIC_SIZE: Final = 4

# --- bounds ----------------------------------------------------------------

#: The bounded prefix :func:`read_header` reads. Measured headers are a couple
#: of hundred bytes, so this is three orders of magnitude of headroom and is
#: still a hard ceiling on an untrusted file.
MAX_HEADER_BYTES: Final = 65_536

#: The ceiling on any single declared string length, checked before allocating.
MAX_STRING_BYTES: Final = 16_384

# ---------------------------------------------------------------------------
# The closed vocabularies the error taxonomy is built from
# ---------------------------------------------------------------------------

#: Every field name an error may carry. The string block is named by POSITION,
#: never by meaning, for the reason in the module docstring.
FIELD_NAMES: Final = frozenset(
    {
        "header_version",
        "save_version",
        "build_changelist",
        "header_string_0",
        "header_string_1",
        "header_string_2",
        "header_string_3",
        "play_duration",
        "datetime_ticks",
        "byte_after_datetime_ticks",
        "editor_object_version",
        "mod_metadata",
        "is_modded",
        "save_identifier",
        "header_tail",
        "body_offset",
    }
)

REASON_DECLARED_LENGTH_ABOVE_CAP: Final = "declared length above the cap"
REASON_UNDECODABLE_TEXT: Final = "declared text is not decodable"
REASON_FILE_UNREADABLE: Final = "save header could not be read"
REASON_OPT_IN_REQUIRED: Final = (
    "rendering a header string requires the explicit reveal_personal_data opt-in"
)

FORMAT_REASONS: Final = frozenset({REASON_DECLARED_LENGTH_ABOVE_CAP, REASON_UNDECODABLE_TEXT})

# ---------------------------------------------------------------------------
# Warnings
# ---------------------------------------------------------------------------

WARN_UNMEASURED_VERSION_PAIR: Final = "unmeasured-version-pair"
WARN_UNEXPECTED_IDENTIFIER_LENGTH: Final = "unexpected-identifier-length"


@dataclass(frozen=True)
class HeaderWarning:
    """One thing the parse flagged and carried anyway.

    Non-negotiable 7: unknown content is flagged and skipped, never fatal and
    never silently wrong. A warning is an echo path like any other, so
    ``subject`` is only ever a version scalar or a length - never a decoded
    string, and never the token.

    Attributes:
        code: One of the module's WARN_* constants.
        subject: The scalar the warning is about, rendered as text.
        detail: One line naming the consequence, echoing no header content.
    """

    code: str
    subject: str
    detail: str


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


def _checked_field(name: str) -> str:
    """Confirm a field name is in the closed vocabulary before it enters a message.

    The static half of the taxonomy gate proves the parameter is a ``str``.
    This is the runtime half: it proves the ``str`` is drawn from
    :data:`FIELD_NAMES`, so the one parameter allowed to be text cannot smuggle
    a decoded value into an error message.

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


class HeaderError(Exception):
    """Base class for every failure this module raises.

    Never raised directly. Every concrete subclass defines its own structured
    ``__init__`` so that no raise site can pass free text.
    """


class HeaderTruncatedError(HeaderError):
    """The file ended before a field this module needed was complete.

    Attributes:
        field: The field being read, from :data:`FIELD_NAMES`.
        offset: The byte offset the read started at.
        needed: How many bytes the field required.
        available: How many bytes remained.
    """

    def __init__(self, *, field: str, offset: int, needed: int, available: int) -> None:
        """Record a truncation.

        Args:
            field: The field being read, from :data:`FIELD_NAMES`.
            offset: The byte offset the read started at.
            needed: How many bytes the field required.
            available: How many bytes remained.
        """
        self.field = _checked_field(field)
        self.offset = offset
        self.needed = needed
        self.available = available
        super().__init__(
            f"save header truncated at {self.field}: offset {offset} needs {needed} bytes,"
            f" {available} available"
        )


class HeaderFormatError(HeaderError):
    """A field declared something structurally impossible.

    Distinct from a truncation on purpose. A truncation means the file is
    SHORT; this means the file declares nonsense, and the distinction decides
    whether a caller should suspect a partial write or a wrong format.

    Attributes:
        field: The field being read, from :data:`FIELD_NAMES`.
        offset: The byte offset the field's length prefix started at.
        reason: One of :data:`FORMAT_REASONS`.
        declared: The byte count the field declared, or None.
        limit: The cap that refused it, or None.
    """

    def __init__(
        self,
        *,
        field: str,
        offset: int,
        reason: str,
        declared: int | None = None,
        limit: int | None = None,
    ) -> None:
        """Record a malformed declaration.

        Args:
            field: The field being read, from :data:`FIELD_NAMES`.
            offset: The byte offset the field's length prefix started at.
            reason: One of :data:`FORMAT_REASONS`.
            declared: The byte count the field declared, if there was one.
            limit: The cap that refused it, if a cap was involved.

        Raises:
            ValueError: The reason is not one of :data:`FORMAT_REASONS`.
        """
        if reason not in FORMAT_REASONS:
            raise ValueError("reason is not one of this module's fixed format reasons")
        self.field = _checked_field(field)
        self.offset = offset
        self.reason = reason
        self.declared = declared
        self.limit = limit
        message = f"malformed save header at {self.field}, offset {offset}: {reason}"
        if declared is not None:
            message += f"; declared {declared}"
        if limit is not None:
            message += f", cap {limit}"
        super().__init__(message)


class UnsupportedHeaderVersionError(HeaderError):
    """The header declares a version this module has no MEASURED layout for.

    Names the integer and nothing else. ADR 0007: a parser that met an unknown
    version and read it against the newest known layout would produce a
    plausible-looking wrong parse rather than a refusal.

    Attributes:
        header_version: The declared version.
    """

    def __init__(self, header_version: int) -> None:
        """Record the refusal.

        Args:
            header_version: The declared version.
        """
        self.header_version = header_version
        super().__init__(f"unsupported save header version {header_version}")


class PersonalDataOptInRequiredError(HeaderError):
    """:func:`reveal_strings` was called without its explicit opt-in.

    The friction is the feature (ADR 0007 decision item 4). This error carries
    no parameters at all, so there is nothing for a caller to put in it.
    """

    def __init__(self) -> None:
        """Record the refusal, with a fixed reason and no caller-supplied content."""
        super().__init__(REASON_OPT_IN_REQUIRED)


class HeaderReadError(HeaderError):
    """A file could not be opened or read.

    A save filename embeds the world name (``clockspeed.data.locate`` strips
    the whole component for exactly that reason), so an :class:`OSError` from
    this path is a leak: its message quotes the filename. The original is
    dropped with ``from None`` and the path is redacted before it arrives here.

    Attributes:
        reason: A fixed reason string.
        redacted_path: A path ALREADY passed through
            ``clockspeed.data.locate.redact()``.
        errno: The underlying errno, or None. A scalar, carried because it is
            the single most useful debugging datum and holds no content.
    """

    def __init__(self, *, reason: str, redacted_path: str, errno: int | None = None) -> None:
        """Record a read failure.

        Args:
            reason: A fixed reason string.
            redacted_path: A path already passed through ``redact()``.
            errno: The underlying errno, if there was one.
        """
        self.reason = reason
        self.redacted_path = redact(redacted_path)
        self.errno = errno
        message = f"{reason}: {self.redacted_path}"
        if errno is not None:
            message += f" (errno {errno})"
        super().__init__(message)


# ---------------------------------------------------------------------------
# Masking
# ---------------------------------------------------------------------------

#: How many hex characters of the digest are rendered. Twelve hex characters
#: is 48 bits, which makes an accidental collision between two worlds on one
#: machine effectively impossible while keeping the rendering short enough to
#: read in a log line.
MASK_DIGEST_CHARACTERS: Final = 12

#: The prefix that marks a rendering as a digest rather than a value, so no
#: reader ever mistakes one for the token itself.
MASK_PREFIX: Final = "world:"


def masked_token(token: str) -> str:
    """Render a world token as a stable digest that discloses none of it.

    The token identifies a world and is personal data - BOOTSTRAP.md section
    2.4 records the literal values as deliberately absent for that reason.

    What a developer actually needs from a debug line is whether two headers
    name the SAME world. A digest answers exactly that question and answers
    nothing else, so it is strictly better than leaving part of the value
    visible: a head-and-tail mask discloses real characters of real personal
    data into every repr and log line that renders one, and a repr is an echo
    path under CLAUDE.md non-negotiable 12 just as much as a log line is.

    This is deliberately NOT reversible and is not meant to be. Nothing in this
    project needs to recover a token from a rendering; the ledger holds the
    real token in a gitignored file and looks it up by value.

    Args:
        token: The identifier as read.

    Returns:
        A prefixed hex digest. An empty token renders as the prefix alone,
        because an empty value has nothing to correlate.
    """
    if not token:
        return MASK_PREFIX
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return MASK_PREFIX + digest[:MASK_DIGEST_CHARACTERS]


# ---------------------------------------------------------------------------
# The returned models
# ---------------------------------------------------------------------------


@dataclass(frozen=True, repr=False)
class SaveHeader:
    """Everything above this layer is allowed to know about a save header.

    THREE OF THE FOUR HEADER STRINGS ARE ABSENT BY DESIGN. The save name, the
    options string and the session name are not fields here and are not even
    decoded by :func:`parse_header`. See the module docstring and ADR 0007.

    Attributes:
        header_version: Drives the STRING LAYOUT and the tail.
        save_version: Carried. It drives body-side decisions this module does
            not make, and conflating the two is the defect the cross-version
            fixture exists to catch.
        build_changelist: The build the save was written by.
        map_name: The level name. A fixed game constant rather than personal
            data, which is why it is the one string that survives to a field.
        world_token: The stable, filename-independent world key.
        play_duration: Seconds.
        datetime_ticks: An int64 tick count.
        byte_after_datetime_ticks: MEASURED IN POSITION, UNVERIFIED IN MEANING.
            Named for where it sits because that is all that is known. It reads
            0x00 on header versions 10 and 13 and on header 14 with save 60,
            and one of 0x10, 0x50, 0x90 or 0xD0 on the eight header-14 save-52
            files in the measured library - so it is NOT a 0/1 flag, and a
            parser calling it "session visibility" is wrong on 8 of 14. Carry
            it, do not interpret it (ADR 0007 decision item 5).
        editor_object_version: An int32. Reads 40 on all 14 measured saves,
            which is what independently anchors the position of the byte above.
        is_modded: The declared flag, verbatim.
        body_offset: THE SEAM. The absolute offset of the chunk magic in the
            data this header was parsed from. Confirmed reachable, not merely
            computed.
        warnings: Everything flagged and carried.
    """

    header_version: int
    save_version: int
    build_changelist: int
    map_name: str
    world_token: str
    play_duration: int
    datetime_ticks: int
    byte_after_datetime_ticks: int
    editor_object_version: int
    is_modded: int
    body_offset: int
    warnings: tuple[HeaderWarning, ...]

    def __repr__(self) -> str:
        """Render versions, a masked token and the seam offset - and nothing else.

        ``map_name`` is deliberately omitted even though it is a game constant.
        Its POSITION is version dependent, so a dispatch bug would put an
        operator-authored string in it, and the repr is the one surface that
        has to stay safe even when the parse is wrong.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(header_version={self.header_version}, "
            f"save_version={self.save_version}, "
            f"build_changelist={self.build_changelist}, "
            f"world_token={masked_token(self.world_token)!r}, "
            f"body_offset={self.body_offset}, "
            f"warnings={len(self.warnings)})"
        )


@dataclass(frozen=True, repr=False)
class HeaderStrings:
    """The opt-in result. RENDER SITE ONLY - never store one of these.

    Every field here is personal data on a real save. The options string
    carries the platform name, a platform account identifier and the player's
    display name in plaintext, and the session name is the operator's own world
    name. ``repr`` is overridden to withhold all of it, because a test runner
    and most loggers repr an object before a human ever chooses what to print.

    Attributes:
        save_name: Present on header 14 only; None on 10 and 13, where the
            field does not exist in the file at all.
        map_name: The level name.
        map_options: The options string.
        session_name: The operator-chosen world name.
    """

    save_name: str | None
    map_name: str
    map_options: str
    session_name: str

    def __repr__(self) -> str:
        """Withhold every value.

        Returns:
            A rendering naming the type and the number of withheld values.
        """
        return f"<{type(self).__name__}: {len(fields(self))} values withheld>"


# ---------------------------------------------------------------------------
# The bounded cursor
# ---------------------------------------------------------------------------


def _string_field(index: int) -> str:
    """Name a string-block slot by POSITION.

    Args:
        index: The zero-based slot.

    Returns:
        The positional field name, for an error message.
    """
    return f"header_string_{index}"


class _Cursor:
    """A bounds-checked forward reader over one buffer.

    Every read goes through :meth:`_require`, so there is no path that indexes
    the buffer without first having said how many bytes it needed and how many
    were there. That is what makes every truncation arrive as a
    :class:`HeaderTruncatedError` rather than as a struct error or an index
    error carrying a fragment of the buffer.
    """

    def __init__(self, data: bytes) -> None:
        """Start at offset zero.

        Args:
            data: The buffer. Never copied, never echoed.
        """
        self._data = data
        self.offset = 0

    def __repr__(self) -> str:
        """Withhold the buffer, deliberately and structurally.

        THIS IS THE LAST THING BETWEEN THE SAVE AND A TRACEBACK RENDERER.
        :func:`parse_header` unbinds its `data` parameter as soon as this object
        exists, so the bytes survive only in `self._data` - and every `_Cursor`
        method that raises leaves `self` in a frame the renderer will print.
        The default `object.__repr__` already withholds it; this states the
        requirement rather than inheriting it by luck, so that making this class
        a dataclass later - whose generated repr would dump the whole file - is
        a deliberate act and not a one-line accident.

        THE BUFFER'S LENGTH IS NOT RENDERED EITHER, and the first cut of this
        method got that wrong. It printed `len(self._data)`, which on a cursor
        reached from `world.load_world_from_bytes` is the EXACT SIZE OF THE SAVE
        FILE - information `object.__repr__` never emitted, added by a change
        whose whole purpose was to reduce what a renderer prints. No arm could
        have flagged it: the sweep matches a planted marker substring, and a
        file size is not a substring of anything. The offset stays because it is
        a position in a parse, derivable from the error that is being raised
        anyway.

        Returns:
            The class name and how far the cursor has read. No bytes, no length.
        """
        return f"<_Cursor at offset {self.offset}>"

    @property
    def remaining(self) -> int:
        """How many bytes are left.

        Returns:
            The count, never negative.
        """
        return len(self._data) - self.offset

    def _require(self, count: int, field: str) -> None:
        """Assert ``count`` bytes are available at the cursor.

        Args:
            count: Bytes needed.
            field: The field being read, from :data:`FIELD_NAMES`.

        Raises:
            HeaderTruncatedError: Fewer than ``count`` bytes remain.
        """
        if count > self.remaining:
            raise HeaderTruncatedError(
                field=field, offset=self.offset, needed=count, available=self.remaining
            )

    def int8(self, field: str) -> int:
        """Read a signed 8-bit integer.

        Args:
            field: The field being read.

        Returns:
            The value.
        """
        self._require(INT8_SIZE, field)
        (value,) = struct.unpack_from("<b", self._data, self.offset)
        self.offset += INT8_SIZE
        return int(value)

    def int32(self, field: str) -> int:
        """Read a signed 32-bit little-endian integer.

        Args:
            field: The field being read.

        Returns:
            The value.
        """
        self._require(INT32_SIZE, field)
        (value,) = struct.unpack_from("<i", self._data, self.offset)
        self.offset += INT32_SIZE
        return int(value)

    def int64(self, field: str) -> int:
        """Read a signed 64-bit little-endian integer.

        Args:
            field: The field being read.

        Returns:
            The value.
        """
        self._require(INT64_SIZE, field)
        (value,) = struct.unpack_from("<q", self._data, self.offset)
        self.offset += INT64_SIZE
        return int(value)

    def skip(self, count: int, field: str) -> None:
        """Step over a run of bytes without reading them.

        Args:
            count: How many bytes to skip.
            field: The field being skipped.
        """
        self._require(count, field)
        self.offset += count

    def _string_extent(self, field: str) -> tuple[int, int]:
        """Read a string's length prefix and return what it spans.

        THE BOUND IS APPLIED HERE, before the remaining length is consulted and
        before any slice is taken. That ordering is the whole point: a file
        declaring a gigabyte must be refused on the DECLARATION rather than
        after an allocation attempt.

        Args:
            field: The field being read.

        Returns:
            ``(byte count, terminator width)``. A zero count is an empty string
            with no payload at all, which is the Unreal convention.

        Raises:
            HeaderFormatError: The declared length exceeds
                :data:`MAX_STRING_BYTES`.
            HeaderTruncatedError: The declared payload runs past the buffer.
        """
        at = self.offset
        count = self.int32(field)
        if count == 0:
            return 0, 0
        if count < 0:
            byte_count = -count * UTF16_CHAR_SIZE
            terminator = UTF16_CHAR_SIZE
        else:
            byte_count = count
            terminator = 1
        if byte_count > MAX_STRING_BYTES:
            raise HeaderFormatError(
                field=field,
                offset=at,
                reason=REASON_DECLARED_LENGTH_ABOVE_CAP,
                declared=byte_count,
                limit=MAX_STRING_BYTES,
            )
        self._require(byte_count, field)
        return byte_count, terminator

    def skip_string(self, field: str) -> None:
        """Step over a length-prefixed string WITHOUT decoding it.

        This is the default path for every personal-data-bearing string. The
        bytes never become a Python string, so there is no value for a
        local-variable dump, a debugger frame or an exception context to carry.

        Args:
            field: The field being skipped.
        """
        byte_count, _terminator = self._string_extent(field)
        self.offset += byte_count

    def string(self, field: str) -> str:
        """Read and DECODE a length-prefixed string.

        THE CURSOR calls this for exactly two fields - the map name, which is a
        game constant, and the identifier. Everything else goes through
        :meth:`skip_string`. That is a statement about this class and NOT about
        the module's whole return surface: :func:`scan_framed_tokens` also
        yields strings out of a header, without going through a cursor at all.
        It widens nothing, because what it returns is shape-restricted before
        it is ever decoded - see its own docstring - but a reader should not be
        left to reconcile the two sentences on their own.

        Args:
            field: The field being read.

        Returns:
            The decoded text, without its trailing null.

        Raises:
            HeaderFormatError: The bytes do not decode. Re-raised ``from None``
                because a :class:`UnicodeDecodeError` message quotes the
                offending bytes, and exception context is an echo path.
        """
        at = self.offset
        byte_count, terminator = self._string_extent(field)
        if byte_count == 0:
            return ""
        encoding = "utf-16-le" if terminator == UTF16_CHAR_SIZE else "utf-8"
        raw = self._data[self.offset : self.offset + byte_count - terminator]
        self.offset += byte_count
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            # THE CS-963 SCRUB, AND THIS SLICE IS THE WORST ONE IN THE MODULE.
            # `raw` is not the whole file, it is EXACTLY one header string - and
            # this method is what `reveal_strings` calls for the options string
            # and the session name, so on a real save it is the platform, the
            # account id and the player display name and nothing else
            # (non-negotiable 12). The raise happens INSIDE this frame, so
            # without the del a locals-showing renderer prints that slice
            # verbatim beside the error that says the bytes did not decode.
            #
            # FOUND BY AN ADVERSARY, NOT BY AN ARM. The two header arms drive a
            # TRUNCATION, which raises in `_string_extent` before `raw` is ever
            # bound - so the one path in this class that binds a save slice
            # across a raise was neither scrubbed nor driven.
            del raw
            raise HeaderFormatError(
                field=field, offset=at, reason=REASON_UNDECODABLE_TEXT, declared=byte_count
            ) from None


# ---------------------------------------------------------------------------
# The parse
# ---------------------------------------------------------------------------


def _version_prologue(cursor: _Cursor) -> tuple[int, int, int]:
    """Read and validate the three leading version fields.

    The version check happens BEFORE a single string is read. A check placed
    after the string block would never fire: an unknown version would first be
    walked against a guessed layout, and would fail as a parse error or, worse,
    succeed against the wrong offsets.

    Args:
        cursor: A cursor positioned at offset zero.

    Returns:
        ``(header version, save version, build changelist)``.

    Raises:
        UnsupportedHeaderVersionError: The version has no measured layout.
    """
    header_version = cursor.int32("header_version")
    if header_version not in SUPPORTED_HEADER_VERSIONS:
        raise UnsupportedHeaderVersionError(header_version)
    return header_version, cursor.int32("save_version"), cursor.int32("build_changelist")


def parse_header(data: bytes) -> SaveHeader:
    """Parse a save header out of the opening bytes of a save.

    Args:
        data: The save bytes. Only a bounded prefix is ever examined, and the
            personal-data-bearing strings are stepped over rather than decoded.

    Returns:
        The header, with ``body_offset`` pointing at the chunk magic.

    Raises:
        UnsupportedHeaderVersionError: The declared header version has no
            measured layout.
        HeaderTruncatedError: The data ends inside the header, or fewer than
            four bytes remain at ``body_offset`` - which would make the seam
            this module promises unverifiable.
        HeaderFormatError: A declared string length is above the cap or the
            bytes do not decode.
    """
    cursor = _Cursor(data)
    # THE CS-963 SCRUB, AND IT IS AN EARLY UNBIND RATHER THAN AN UNWIND GUARD.
    # This frame binds the WHOLE SAVE, and `raise ... from exc` up in
    # `world.load_world_from_bytes` puts this frame in the rendered traceback as
    # the CAUSE - so `pytest --showlocals` prints the header's options string,
    # which carries the platform, the account id and the player display name in
    # PLAINTEXT (non-negotiable 12, `BOOTSTRAP.md` section 2.2).
    #
    # UNBINDING HERE IS STRICTLY STRONGER THAN A GUARD ON THE WAY OUT, because
    # the name is gone for the function's whole lifetime rather than only while
    # unwinding - there is no window, and no later-added `return` path that
    # forgets to pass through a handler. The buffer itself lives on inside the
    # cursor, which is why `_Cursor` withholds it from `__repr__`: that is what a
    # renderer reads, and it is the only thing left between the two.
    del data
    header_version, save_version, build_changelist = _version_prologue(cursor)

    # The string block, dispatched on the HEADER version alone. Header 14 adds
    # a save name at the FRONT, which shifts every later slot by one - the
    # exact off-by-one ADR 0007 exists for.
    slot = 0
    if header_version >= HEADER_VERSION_WITH_SAVE_NAME:
        cursor.skip_string(_string_field(slot))
        slot += 1
    map_name = cursor.string(_string_field(slot))
    slot += 1
    cursor.skip_string(_string_field(slot))
    slot += 1
    cursor.skip_string(_string_field(slot))

    # The fixed block, identical on every measured header version.
    play_duration = cursor.int32("play_duration")
    datetime_ticks = cursor.int64("datetime_ticks")
    byte_after_datetime_ticks = cursor.int8("byte_after_datetime_ticks")
    editor_object_version = cursor.int32("editor_object_version")
    cursor.skip_string("mod_metadata")
    is_modded = cursor.int32("is_modded")
    world_token = cursor.string("save_identifier")

    if header_version >= HEADER_VERSION_WITH_TAIL:
        cursor.skip(HEADER_TAIL_SIZE, "header_tail")

    body_offset = cursor.offset
    # The seam promise, confirmed rather than assumed. The magic's VALUE is the
    # chunk walker's business; only its reachability is this module's.
    cursor.skip(CHUNK_MAGIC_SIZE, "body_offset")

    return SaveHeader(
        header_version=header_version,
        save_version=save_version,
        build_changelist=build_changelist,
        map_name=map_name,
        world_token=world_token,
        play_duration=play_duration,
        datetime_ticks=datetime_ticks,
        byte_after_datetime_ticks=byte_after_datetime_ticks,
        editor_object_version=editor_object_version,
        is_modded=is_modded,
        body_offset=body_offset,
        warnings=_warnings_for(header_version, save_version, world_token),
    )


def _warnings_for(
    header_version: int, save_version: int, world_token: str
) -> tuple[HeaderWarning, ...]:
    """Flag what was unattested without refusing any of it.

    Non-negotiable 7 and ADR 0007 decision item 3: unknown content is flagged
    and carried, never fatal. Every subject below is a SCALAR - a version pair
    or a length - so a warning cannot become an echo path for the token or for
    any header string.

    Args:
        header_version: The declared header version.
        save_version: The declared save version.
        world_token: The identifier as read, used only for its length.

    Returns:
        The warnings, in a stable order.
    """
    found: list[HeaderWarning] = []
    if (header_version, save_version) not in MEASURED_VERSION_PAIRS:
        found.append(
            HeaderWarning(
                code=WARN_UNMEASURED_VERSION_PAIR,
                subject=f"{header_version}/{save_version}",
                detail=(
                    "header and save version pair is outside the measured library;"
                    " the layout was dispatched on the header version alone"
                ),
            )
        )
    if len(world_token) != WORLD_TOKEN_LENGTH:
        found.append(
            HeaderWarning(
                code=WARN_UNEXPECTED_IDENTIFIER_LENGTH,
                subject=str(len(world_token)),
                detail=(
                    f"save identifier is not the measured {WORLD_TOKEN_LENGTH} characters;"
                    " carried as read rather than refused"
                ),
            )
        )
    return tuple(found)


def read_header(path: Path | str) -> SaveHeader:
    """Read a bounded prefix of a file and parse its header.

    Opens for READ ONLY. Nothing in this package opens a save for write, and
    the save directory is never written to at all (non-negotiable 1).

    Args:
        path: The file to read. A copy of a save, never the save in place -
            the game holds handles during autosave.

    Returns:
        The parsed header. ``body_offset`` is an absolute offset into the FILE,
        so it stays correct despite the bounded read.

    Raises:
        HeaderReadError: The file could not be opened or read. The path is
            redacted and the original OSError is dropped rather than chained,
            because its message quotes the filename and a save filename embeds
            the world name.
    """
    target = Path(path)
    try:
        with target.open("rb") as handle:
            data = handle.read(MAX_HEADER_BYTES)
    except OSError as error:
        raise HeaderReadError(
            reason=REASON_FILE_UNREADABLE,
            redacted_path=redact(target),
            errno=error.errno,
        ) from None
    # THE CS-963 SCRUB. This frame holds a bounded PREFIX of the file, which is
    # precisely the personal-data-bearing region - the header strings are at the
    # front. A refusal out of `parse_header` unwinds through here, and
    # `world.load_world` chains it, so a locals-showing renderer prints the
    # options string out of THIS frame even once the callee's own is clean.
    # Scrubbing only the callee would have repaired one of two (non-negotiable 12).
    try:
        return parse_header(data)
    except BaseException:
        del data
        raise


# ---------------------------------------------------------------------------
# The non-parsing scan - CS-1087
# ---------------------------------------------------------------------------
#
# WHY A SECOND WAY TO REACH THE IDENTIFIER EXISTS AT ALL, AND WHY IT IS NOT A
# SECOND PARSER. A header that refuses to parse still holds its bytes, and the
# identifier is one of them: the refusal usually happens at the version
# prologue, BEFORE a single string is read, so the whole string block is
# untouched on disk. The commit gate's world-token blocklist needs the VALUE
# and nothing else about the file - it never needs a layout, a version or an
# offset - and a token it cannot obtain is a token that commits.
#
# So the functions below dispatch on no version, decode no field, invent no
# offset and promise no seam. They look for one SHAPE, in the two framings
# ``_Cursor._string_extent`` already admits, and return only values that match
# it. They live HERE rather than in the caller for two reasons: the framing
# they depend on is this module's measurement, and this module is the one that
# already scrubs a bounded save prefix out of its frames on the way out
# (CS-963). A scan bound in the caller's frame would reproduce that defect one
# level up, in a file whose own traceback cannot be honestly redacted.
#
# WHAT THIS CAN AND CANNOT RETURN. The values are shape-restricted before they
# exist as strings - exactly :data:`WORLD_TOKEN_LENGTH` characters drawn from
# :data:`TOKEN_ALPHABET`, then a null terminator. The options string cannot come
# close: it carries ``?`` and ``=``, which are outside the alphabet, and the
# measured map name is a game constant of another length. SHAPE ALONE DOES NOT
# EXCLUDE A PLAYER-CHOSEN STRING, though, and the earlier wording here claimed
# it did. A save name, a session name or a display name of exactly 22 alphabet
# characters is framed identically to the identifier.
#
# THE SAVE NAME AND THE SESSION NAME ARE EXCLUDED BY POSITION, AND ONLY ON
# EVIDENCE (CS-1097, CS-1114). On header 14 the save name is the FIRST string
# of the string block, which starts at :data:`FIRST_STRING_SLOT_OFFSET` on
# every measured header version because the prologue before it is the same
# three int32 fields on 10, 13 and 14. The session name follows a fixed number
# of framed strings in the parser's own field order: after the save name, the
# map name and the options string on 14, after the map name and the options
# string below it. The identifier is the LAST string, after the fixed block,
# and sits in neither slot on any measured layout.
#
# An offset alone is no evidence, because the scan exists precisely for bytes
# the parser refuses. So :func:`_personal_slot_offsets` first reads the three
# prologue fields out of the same bytes and requires each to be PLAUSIBLE - see
# :data:`_PLAUSIBLE_VERSION_CEILING` - and a header version whose layout the
# parser's own dispatch gives a save name to. It then walks the string chain
# with the parser's own cursor, and a slot is refused only if every string
# before it frames. Refused slots are skipped before they are decoded and
# before they spend a slot of the candidate cap.
#
# THE RESIDUE, stated rather than hidden. An unmeasured future layout at or
# above header 14 is READ AS header 14's, which is the extrapolation ADR 0007
# forbids the parser: if it put the identifier in slot 0 or at the session
# slot behind a plausible prologue, it would be missed. A header version below
# every measured one, or a prologue damaged out of range, refuses nothing, so
# a false admission there only widens what the gate REFUSES to commit.

#: The base64url alphabet the measured identifier is drawn from. A character
#: outside it disqualifies a candidate outright, which is what keeps this a
#: shape match rather than a string scrape.
# S105 is suppressed with its code rather than blanket-ignored, because a bare
# suppression is itself banned. Bandit sees a long opaque literal and reads it
# as a secret; this is the base64url ALPHABET, public knowledge, and it holds
# no value at all.
TOKEN_ALPHABET: Final = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"  # noqa: S105

#: The alphabet as raw byte values, so the scan never decodes to test.
_TOKEN_BYTES: Final = frozenset(TOKEN_ALPHABET.encode("ascii"))

#: The two length prefixes a :data:`WORLD_TOKEN_LENGTH` string can carry.
#: POSITIVE is a byte count INCLUDING the one-byte terminator; NEGATIVE is a
#: UTF-16-LE CHARACTER count including its two-byte terminator. Both are the
#: framing ``_Cursor._string_extent`` reads, spelled here as the literal bytes
#: a scan can search for rather than re-derived per offset.
_NARROW_COUNT_PREFIX: Final = struct.pack("<i", WORLD_TOKEN_LENGTH + 1)
_WIDE_COUNT_PREFIX: Final = struct.pack("<i", -(WORLD_TOKEN_LENGTH + 1))

#: How many DISTINCT candidates one buffer may yield, PER FRAMING. What it
#: bounds is the size of the caller's blocklist and nothing else: the WALK is
#: already bounded by :data:`MAX_HEADER_BYTES`, so a buffer cannot cost more
#: work than that however many hits it holds, and the gate's aggregate wall
#: clock and its file cap are the caller's, unchanged.
#:
#: IT COUNTS AFTER DE-DUPLICATION AND PER FRAMING, and both halves are
#: repairs of a measured loss rather than taste. Counting raw hits let one
#: value repeated to the cap hide a DIFFERENT value behind it, and a single
#: shared budget let a narrow-framed buffer spend the whole of it before the
#: wide framing was scanned at all - so a real token was dropped in both
#: shapes. A caller is told when the cap truncates, because a bound that
#: silently shrinks a blocklist is a fail-open.
MAX_SCANNED_TOKENS: Final = 16

#: The int32 fields of the version prologue ``_version_prologue`` reads before
#: the string block: header version, save version, build changelist. MEASURED
#: identical on header versions 10, 13 and 14 (BOOTSTRAP.md section 2.4).
_PROLOGUE_INT32_FIELDS: Final = 3

#: The file offset of the FIRST string slot - the save name on header 14, the
#: map name on 10 and 13 - on every measured header version. The scan refuses a
#: candidate framed here (CS-1097) only behind a plausible prologue whose
#: header version gives the layout a save name (CS-1114).
FIRST_STRING_SLOT_OFFSET: Final = _PROLOGUE_INT32_FIELDS * INT32_SIZE

#: The largest header or save version a prologue may declare and still count
#: as EVIDENCE of a string block behind it. A BOUND, NOT A MEASUREMENT: it is
#: sixteen bits of headroom over every measured value, so a future version is
#: still read as one while bytes that are no prologue at all - text, a count, a
#: damaged field - mostly are not. Erring above it refuses nothing, which only
#: widens what the gate refuses to commit.
_PLAUSIBLE_VERSION_CEILING: Final = 0xFFFF

#: The smallest plausible header version: the oldest one measured. Below it no
#: layout is known at all, so no slot is refused.
_MIN_PLAUSIBLE_HEADER_VERSION: Final = min(SUPPORTED_HEADER_VERSIONS)

#: The smallest plausible save version: the oldest one measured.
_MIN_PLAUSIBLE_SAVE_VERSION: Final = min(save for _header, save in MEASURED_VERSION_PAIRS)

#: The strings the parser reads between the first slot and the session name,
#: in its own order, after the save name where the layout has one: the map
#: name and the options string (``parse_header`` slots map, options, session).
_STRINGS_BEFORE_SESSION_NAME: Final = 2


def _plausible_prologue(header_version: int, save_version: int, build_changelist: int) -> bool:
    """Whether three leading int32 fields read as a version prologue.

    Args:
        header_version: The first field.
        save_version: The second field.
        build_changelist: The third field.

    Returns:
        True only if every field is inside its plausible range.
    """
    return (
        _MIN_PLAUSIBLE_HEADER_VERSION <= header_version <= _PLAUSIBLE_VERSION_CEILING
        and _MIN_PLAUSIBLE_SAVE_VERSION <= save_version <= _PLAUSIBLE_VERSION_CEILING
        and build_changelist >= 0
    )


def _personal_slot_offsets(data: bytes) -> frozenset[int]:
    """The count-prefix offsets of the save-name and session-name slots, on evidence.

    THE EVIDENCE IS READ FROM THE SAME BYTES. The three prologue fields must be
    plausible (:func:`_plausible_prologue`); otherwise nothing is refused. The
    save-name slot is then :data:`FIRST_STRING_SLOT_OFFSET` if and only if the
    header version is one the parser's dispatch gives a save name to. The
    session-name slot is found by stepping over the strings before it with the
    parser's own :class:`_Cursor`, so the framing, the string cap and the
    truncation rule are the parser's; a string that does not frame stops the
    walk and the session slot is not refused.

    NO SLOT IS DECODED. The cursor only steps over strings, so nothing here
    becomes a Python string, and the buffer is scrubbed out of this frame on
    the unwind exactly as :func:`scan_framed_tokens` scrubs it (CS-963).

    Args:
        data: The buffer being scanned, anchored at file offset zero.

    Returns:
        The refused offsets, possibly empty.
    """
    offsets: set[int] = set()
    cursor: _Cursor | None = None
    try:
        if len(data) < FIRST_STRING_SLOT_OFFSET:
            return frozenset()
        header_version, save_version, build_changelist = struct.unpack_from(
            "<" + "i" * _PROLOGUE_INT32_FIELDS, data, 0
        )
        if not _plausible_prologue(header_version, save_version, build_changelist):
            return frozenset()
        cursor = _Cursor(data)
        cursor.offset = FIRST_STRING_SLOT_OFFSET
        slot = 0
        if header_version >= HEADER_VERSION_WITH_SAVE_NAME:
            offsets.add(cursor.offset)
            cursor.skip_string(_string_field(slot))
            slot += 1
        for _ in range(_STRINGS_BEFORE_SESSION_NAME):
            cursor.skip_string(_string_field(slot))
            slot += 1
        offsets.add(cursor.offset)
    except (HeaderTruncatedError, HeaderFormatError):
        # The chain did not frame, so the slots past the break are unknown.
        pass
    except BaseException:
        del data, cursor
        raise
    del data, cursor
    return frozenset(offsets)


def _framed_token_at(data: bytes, start: int, stride: int) -> str | None:
    """The token framed at ``start``, or None if what is there is not one.

    Args:
        data: The buffer being scanned.
        start: The offset of the first payload byte, just past the count.
        stride: 1 for the narrow framing, :data:`UTF16_CHAR_SIZE` for the wide
            one. It is also the terminator width, because the two are the same
            number in both framings.

    Returns:
        The decoded candidate, or None. Nothing outside the alphabet is ever
        decoded, so a non-candidate never becomes a Python string at all.
    """
    end = start + WORLD_TOKEN_LENGTH * stride
    if end + stride > len(data):
        return None
    for index in range(start, end, stride):
        if data[index] not in _TOKEN_BYTES:
            return None
        # The wide framing's high byte must be zero for an alphabet character.
        # Without this a two-byte sequence whose LOW byte happens to be
        # alphabet would pass, which is a scrape and not a shape match.
        if stride == UTF16_CHAR_SIZE and data[index + 1] != 0:
            return None
    if data[end : end + stride] != bytes(stride):
        return None
    return data[start:end:stride].decode("ascii")


def scan_framed_tokens(data: bytes) -> tuple[tuple[str, ...], bool]:
    """Find identifier-SHAPED framed strings in a buffer, parsing nothing.

    THE MATCH IS THE FRAMING PLUS THE SHAPE, not a search for a run of
    characters. A candidate must carry the int32 count the module's own string
    framing would write for a :data:`WORLD_TOKEN_LENGTH` string, then exactly
    that many characters from :data:`TOKEN_ALPHABET`, then the terminator that
    count implies. A bare 22-character run in the middle of a file matches
    nothing, and neither does a 21- or 23-character framed one.

    THE SAVE-NAME AND SESSION-NAME SLOTS ARE NEVER CANDIDATES, ON EVIDENCE. A
    count prefix at an offset :func:`_personal_slot_offsets` returns is skipped
    in both framings, undecoded and uncounted against the cap: behind a
    plausible prologue those slots hold the player-chosen save name and
    session name, and on no measured layout do they hold the identifier.
    Behind bytes that are no prologue, offset 12 is an ordinary candidate. The
    offsets are file-anchored, which holds because every caller here passes a
    prefix read from offset zero.

    A MEASURED LIMIT, NOT A CLOSED ONE: a 22-character session name is refused
    only where the chain of strings before it frames. A session name in a
    buffer whose options string is truncated or damaged is still admitted,
    because no reader can say where that slot begins.

    UNMEASURED, AND LABELLED RATHER THAN ASSUMED: every header in the measured
    library frames its identifier with a POSITIVE count, so the wide framing
    below has never been seen on a real save. It is handled because
    ``_Cursor._string_extent`` admits it and a scan that ignored it would be
    making a claim about real files that no probe supports.

    THE BUFFER IS SCRUBBED OUT OF THIS FRAME ON THE UNWIND. It is the CALLER's
    bounded prefix and this frame binds it BARE - an undotted local that a
    locals-showing renderer prints verbatim, which the sweep in
    tests/save/test_properties.py rates the worst kind of holder there is. The
    parse path never had one: a refusal there leaves the bytes reachable only
    through a cursor attribute. Without the unbind below, this function was the
    first frame in the module to hold a save prefix bare across a raise
    (CS-963, non-negotiable 12).

    Args:
        data: The bytes to scan. A bounded prefix in every caller here, and
            never decoded except where the shape already matched.

    Returns:
        ``(candidates, truncated)``. The candidates are in file order and
        de-duplicated; ``truncated`` says the per-framing cap stopped the scan
        with candidates still unexamined, so the result is a SUBSET and the
        caller owes its own user that fact.
    """
    hits: list[tuple[int, str]] = []
    truncated = False
    try:
        refused = _personal_slot_offsets(data)
        for prefix, stride in ((_NARROW_COUNT_PREFIX, 1), (_WIDE_COUNT_PREFIX, UTF16_CHAR_SIZE)):
            # A budget PER FRAMING. Shared, a narrow-framed buffer could spend
            # the whole of it and the wide framing would never be scanned.
            admitted: set[str] = set()
            at = data.find(prefix)
            while at != -1:
                # A personal slot is refused BEFORE it is decoded and BEFORE the
                # cap is tested, so a save name or session name never becomes a
                # string and never spends a slot a genuine identifier later
                # needs (CS-1097, CS-1114).
                if at in refused:
                    at = data.find(prefix, at + 1)
                    continue
                candidate = _framed_token_at(data, at + INT32_SIZE, stride)
                # The cap is tested against DISTINCT values, so a value
                # repeated to the cap cannot hide a different one behind it.
                if candidate is not None and candidate not in admitted:
                    if len(admitted) >= MAX_SCANNED_TOKENS:
                        truncated = True
                        break
                    admitted.add(candidate)
                    hits.append((at, candidate))
                at = data.find(prefix, at + 1)
    except BaseException:
        del data
        raise
    del data
    found: list[str] = []
    seen: set[str] = set()
    # Sorted by OFFSET, because the two framings are searched one after the
    # other and file order is what the docstring promises. A caller comparing
    # two runs of this function over the same bytes would otherwise be reading
    # an order that depends on which framing happened to be scanned first.
    for _at, candidate in sorted(hits):
        if candidate in seen:
            continue
        seen.add(candidate)
        found.append(candidate)
    return tuple(found), truncated


def scan_world_tokens(path: Path | str) -> tuple[tuple[str, ...], bool]:
    """Recover identifier-shaped values from a file WITHOUT parsing it.

    THIS IS FOR A HEADER THAT WILL NOT PARSE and for nothing else. A file that
    parses has :func:`read_header`, which returns the identifier the layout
    says is the identifier; this one returns everything of that SHAPE and
    cannot tell the caller which of them the layout would have chosen. A
    caller that used it on a parseable file would be preferring a guess to a
    measurement.

    Opens for READ ONLY and reads at most :data:`MAX_HEADER_BYTES`, which are
    the same access and the same bound :func:`read_header` already takes
    (non-negotiable 1 forbids WRITING to a save, never reading one).

    THE PREFIX IS SCRUBBED ON BOTH PATHS. This frame binds a bounded prefix of
    the file, which is precisely the personal-data-bearing region - the header
    strings are at the front - and a caller that chains an exception through
    here puts this frame in a rendered traceback. The unbind is unconditional
    rather than an unwind guard, so there is no later-added return path that
    forgets it (CS-963, non-negotiable 12).

    Args:
        path: The file to read.

    Returns:
        ``(candidates, truncated)``, exactly as :func:`scan_framed_tokens`
        returns them. An empty candidate tuple is the honest answer for a file
        with nothing of this shape in its prefix - truncated or overwritten
        before the identifier, or carrying the characters with a damaged count
        prefix, which frames nothing this scan can find.

    Raises:
        HeaderReadError: The file could not be opened or read. The path is
            redacted and the original OSError is dropped rather than chained,
            because its message quotes the filename and a save filename embeds
            the world name.
    """
    target = Path(path)
    try:
        with target.open("rb") as handle:
            data = handle.read(MAX_HEADER_BYTES)
    except OSError as error:
        raise HeaderReadError(
            reason=REASON_FILE_UNREADABLE,
            redacted_path=redact(target),
            errno=error.errno,
        ) from None
    try:
        result = scan_framed_tokens(data)
    except BaseException:
        del data
        raise
    del data
    return result


def reveal_strings(data: bytes, *, reveal_personal_data: bool = False) -> HeaderStrings:
    """Decode the header strings, including the personal-data-bearing ones.

    THE ONLY SANCTIONED WAY TO OBTAIN THESE VALUES, AND IT IS DELIBERATELY
    AWKWARD. ADR 0007 decision item 4: the result is render-site only. Do not
    store it on a long-lived object, do not log it, do not put it in exception
    context, and do not pass it to ``redact()`` expecting help -
    ``clockspeed.data.locate.redact()`` holds no needle for a session name read
    out of a header, because that string is not knowable in advance.

    The opt-in is keyword-only with a False default, so reaching these values
    is always a deliberate act at the call site and never a forgotten argument.

    Args:
        data: The save bytes.
        reveal_personal_data: Must be passed as True. The caller is asserting
            that this call site is a render site.

    Returns:
        The strings, with ``save_name`` None on header versions 10 and 13,
        where the field does not exist in the file.

    Raises:
        PersonalDataOptInRequiredError: The opt-in was not passed.
        UnsupportedHeaderVersionError: The opt-in is not a bypass for the
            version dispatch - an unmeasured layout is still refused.
        HeaderTruncatedError: The data ends inside the string block.
        HeaderFormatError: A declared length is above the cap, or the bytes do
            not decode.
    """
    if not reveal_personal_data:
        raise PersonalDataOptInRequiredError
    cursor = _Cursor(data)
    # THE CS-963 SCRUB, AND IT IS AN EARLY UNBIND RATHER THAN AN UNWIND GUARD.
    # This frame binds the WHOLE SAVE, and `raise ... from exc` up in
    # `world.load_world_from_bytes` puts this frame in the rendered traceback as
    # the CAUSE - so `pytest --showlocals` prints the header's options string,
    # which carries the platform, the account id and the player display name in
    # PLAINTEXT (non-negotiable 12, `BOOTSTRAP.md` section 2.2).
    #
    # UNBINDING HERE IS STRICTLY STRONGER THAN A GUARD ON THE WAY OUT, because
    # the name is gone for the function's whole lifetime rather than only while
    # unwinding - there is no window, and no later-added `return` path that
    # forgets to pass through a handler. The buffer itself lives on inside the
    # cursor, which is why `_Cursor` withholds it from `__repr__`: that is what a
    # renderer reads, and it is the only thing left between the two.
    del data
    header_version, _save_version, _build_changelist = _version_prologue(cursor)

    # THE DECODED STRINGS NEED THEIR OWN SCRUB, AND THIS ONE IS WORSE THAN THE
    # BUFFER. Unbinding `data` above puts the raw bytes out of a renderer's reach,
    # but this function goes on to decode the options string into a local of its
    # own - and the strings are read one after another, so a refusal on the LAST
    # one unwinds with the earlier ones already bound and fully decoded. What a
    # locals-showing renderer then prints is not bytes a reader has to interpret,
    # it is the platform, the account id and the player display name as text
    # (non-negotiable 12, `BOOTSTRAP.md` section 2.2).
    #
    # THE OPT-IN IS NOT A DEFENCE HERE. It says the CALLER is a render site; it
    # says nothing about where a traceback out of this frame ends up, and ADR 0007
    # decision item 4 forbids putting these values in exception context at all.
    #
    # ALL FOUR ARE PRE-BOUND so the scrub is unconditional: `del` on a name that
    # was never bound raises, and that would MASK the real refusal with a
    # `NameError` from the handler.
    save_name: str | None = None
    map_name = ""
    map_options = ""
    session_name = ""
    try:
        slot = 0
        if header_version >= HEADER_VERSION_WITH_SAVE_NAME:
            save_name = cursor.string(_string_field(slot))
            slot += 1
        map_name = cursor.string(_string_field(slot))
        slot += 1
        map_options = cursor.string(_string_field(slot))
        slot += 1
        session_name = cursor.string(_string_field(slot))

        return HeaderStrings(
            save_name=save_name,
            map_name=map_name,
            map_options=map_options,
            session_name=session_name,
        )
    except BaseException:
        del save_name, map_name, map_options, session_name
        raise
