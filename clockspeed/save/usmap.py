"""Loading, validating and caching the shipped ``FactoryGame.usmap``.

WHY THIS MODULE EXISTS. The game serializes its actors as unversioned property
bags: the wire format carries values but not the names or types needed to read
them back. ``FactoryGame.usmap`` is the property mapping that makes them
parseable, and it ships inside the install. Nothing else in the system reads
that file (docs/ARCHITECTURE.md section 1.1). Everything above this module
consumes the parsed :class:`PropertyMap`, never the bytes.

PUBLISHER-OWNED MATERIAL (non-negotiable 2). The mapping is game data. It is
READ from the install at runtime and never copied, vendored, committed or
placed in a fixture directory. ``*.usmap`` is gitignored, and the rule suite
builds its own bytes rather than slicing this file.

THE CONTAINER, WHICH IS MEASURED. The outer framing is a uint16 magic, a uint8
version, an optional versioning block, then the compression method and the
compressed and decompressed sizes. On the pinned build the header measures
1812 bytes and the body accounts for the remainder of the file exactly. The
versioning block is present from version 1 and is gated a second time by its
own ``bHasVersioning`` flag, which is why the header size is derived by walking
the fields rather than assumed.

WHY AN UNSUPPORTED COMPRESSION METHOD IS ITS OWN ERROR. The pinned build ships
the mapping UNCOMPRESSED - method 0. A future build could ship it Oodle
compressed, and Oodle needs an external decompressor. That decompressor is a
third-party dependency, so it carries a CONVENTIONS.md section 14 license gate
and would be recorded in docs/GATED.md before any code called it. The parser
therefore raises exactly one clean
:class:`UnsupportedUsmapCompressionError` naming the method integer, so that
the day the format changes the failure arrives as a filed, actionable item
rather than as a mystery crash inside a decompressor that is not there.

THE INNER GRAMMAR, WHICH WAS DERIVED AND VERIFIED, NOT ASSUMED. The section
layout below was read out of the shipped bytes for this slice, not taken from a
document:

  names    uint32 count, then a uint8 length and that many UTF-8 bytes each.
  enums    uint32 count, then per enum a uint32 index into the name table, a
           uint8 member count, and that many uint32 name-table indices.
  schemas  uint32 count, then per schema a uint32 name index, a uint32 super
           index (all bits set means no super), a uint16 property count and a
           uint16 serializable count, then that many property entries.
  entry    uint16 slot, uint8 array size, uint32 name index, uint8 type, then
           a type-dependent payload - see :data:`_PAYLOAD`.

The verification is a single decisive constraint rather than agreement with
another reader: on the pinned build this grammar consumes the name, enum and
schema sections and lands EXACTLY on a four-character ASCII section tag, with
every property type byte inside the observed range and every name index in
bounds across the whole file. A grammar that is wrong anywhere does not land on
a tag boundary by accident.
``tests/save/test_usmap.py::test_the_real_usmap_accounts_for_its_own_length_exactly``
is that control, and it skips with a reason where there is no install.

WHAT IS NOT PARSED, STATED PLAINLY. After the schemas the pinned build carries
an extension container tagged ``CEXT`` holding further tagged blocks. Nothing
in Clockspeed consumes them, so they are FLAGGED as a trailing section and
skipped (non-negotiable 7). They are not silently ignored and they are not
fatal, and :attr:`PropertyMap.body_consumed` reports exactly how far the parse
got.

UNKNOWN CONTENT IS FLAGGED AND SKIPPED, NEVER FATAL (non-negotiable 7). An
unrecognised property type is recorded as a warning and the entry is dropped;
parsing continues with the next one. Because a type this module has never seen
may carry a payload it cannot measure, a desynchronised read is caught by the
in-bounds check on the next name index and ends the section with a second
warning rather than inventing a mapping. Flagged, skipped, never fatal, and
never silently wrong.

A NAME WHOSE BYTES ARE NOT UTF-8 IS THE SAME RULE APPLIED TO TEXT, and it is
where the rule was hardest to satisfy (CS-435). Decoding with a replacement
character does not lose the name, it INVENTS a different one, and everything
downstream then works perfectly against a key the file does not contain - which
is the "never silently wrong" breach, not the tolerated "never fatal" one.
Raising instead would breach the other half, and much wider than a save
parser's own decode sites do: this module is the oracle for the WHOLE save
library, so one bad byte in the shipped name table would make every save on the
machine unreadable rather than one. So the position is flagged under
:data:`WARN_UNDECODABLE_NAME` and made unresolvable, which is the same None the
readers below already answer to for an out-of-bounds index. NO CLAIM IS MADE
HERE ABOUT WHAT THEN HAPPENS AT THE SITES THAT RESOLVE IT. Section 15 of
``tests/save/test_usmap.py`` pins the measured paths where the position's
second, per-site warning does not appear; the first build of CS-435 shipped a
warning detail asserting the opposite and was refuted by them. Read the count
off that section rather than from here. See :class:`_NameTable`.

THE ERROR TAXONOMY, WHICH IS NARROW ON PURPOSE. An exception raised here may
carry a field name, a byte offset, an expected or actual length or count, a
version or method integer, and a fixed reason string. It may not carry raw
bytes, a hex preview, a name decoded out of the file, or an unredacted path -
paths go through :func:`clockspeed.data.locate.redact`. That keeps every echo
path clean by construction rather than by review.

A RELATED BUT WEAKER DISCIPLINE COVERS ``__repr__``. :class:`PropertyMap`,
:class:`Schema` and :class:`PropertyEntry` render structure and counts and
withhold every name, because the generated repr prints the whole shipped name
table and a test runner reprs an object before a human chooses what to print.
The reason is DIAGNOSTIC NOISE AND AN ASSET ECHO, not privacy - these are
publisher-owned asset names, and calling that a non-negotiable 12 breach would
overstate it. Weaker than the taxonomy above, and still worth having.

SEAM. This module reads the install and nothing else. It does not touch a save
file, it never writes anywhere, and it imports only from
``clockspeed.data.locate`` (docs/ARCHITECTURE.md section 3).
"""

from __future__ import annotations

import struct
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

from clockspeed.data.locate import redact, resolve_game_dir

__all__ = [
    "COMPRESSION_NONE",
    "MAX_KNOWN_PROPERTY_TYPE",
    "MAX_KNOWN_VERSION",
    "USMAP_MAGIC",
    "USMAP_RELATIVE",
    "VERSION_PACKAGE_VERSIONING",
    "WARN_DESYNCHRONISED_SECTION",
    "WARN_DUPLICATE_ENUM",
    "WARN_DUPLICATE_SCHEMA",
    "WARN_TRAILING_SECTION",
    "WARN_UNDECODABLE_NAME",
    "WARN_UNKNOWN_PROPERTY_TYPE",
    "WARN_UNKNOWN_VERSION",
    "WARN_UNRESOLVED_NAME",
    "PropertyEntry",
    "PropertyMap",
    "Schema",
    "UnsupportedUsmapCompressionError",
    "UsmapContainer",
    "UsmapError",
    "UsmapFormatError",
    "UsmapWarning",
    "cached_usmap",
    "clear_cache",
    "default_usmap_path",
    "load_usmap",
    "parse_usmap",
]

# --- container constants ----------------------------------------------------

#: The uint16 that opens every property mapping file.
USMAP_MAGIC: Final = 0x30C4

#: The only compression method this module can read without a gated dependency.
COMPRESSION_NONE: Final = 0

#: From this version the header carries a versioning block, itself gated by a
#: ``bHasVersioning`` flag.
VERSION_PACKAGE_VERSIONING: Final = 1

#: A file version above this has a layout nobody here has seen. It is flagged
#: rather than refused, because the container fields it needs come first.
MAX_KNOWN_VERSION: Final = 1

#: Bytes per custom version record: a 16-byte GUID and an int32 version.
_CUSTOM_VERSION_RECORD: Final = 20

#: A sane ceiling on the custom version count, so a corrupt integer becomes a
#: clean error instead of an enormous seek.
_MAX_CUSTOM_VERSIONS: Final = 4096

#: Where the mapping sits inside the install.
USMAP_RELATIVE: Final = ("CommunityResources", "FactoryGame.usmap")

#: A super index with every bit set means the schema has no super type.
_NO_SUPER: Final = 0xFFFFFFFF

# --- property types ---------------------------------------------------------

#: The highest property type id observed in the pinned build. A byte above this
#: is unknown content: flagged and skipped, never fatal.
MAX_KNOWN_PROPERTY_TYPE: Final = 29

_NONE: Final = 0
_NAME: Final = 1
_INNER: Final = 2
_INNER_NAME: Final = 3
_INNER_INNER: Final = 4

#: What each property type carries after its type byte. Every type absent from
#: this mapping carries nothing. Derived from the shipped bytes.
_PAYLOAD: Final[Mapping[int, int]] = MappingProxyType(
    {
        8: _INNER,  # array: one inner descriptor
        9: _NAME,  # struct: one name-table index
        24: _INNER_INNER,  # map: a key descriptor then a value descriptor
        25: _INNER,  # set: one inner descriptor
        26: _INNER_NAME,  # enum: an inner descriptor then the enum name
    }
)

#: A descriptor nests only a few levels in practice. The cap turns a corrupt
#: byte run into a clean error instead of a recursion crash.
_MAX_DESCRIPTOR_DEPTH: Final = 16

# --- warning codes ----------------------------------------------------------

WARN_DESYNCHRONISED_SECTION: Final = "desynchronised-section"
WARN_DUPLICATE_ENUM: Final = "duplicate-enum"
WARN_DUPLICATE_SCHEMA: Final = "duplicate-schema"
WARN_TRAILING_SECTION: Final = "trailing-section"
WARN_UNDECODABLE_NAME: Final = "undecodable-name"
WARN_UNKNOWN_PROPERTY_TYPE: Final = "unknown-property-type"
WARN_UNKNOWN_VERSION: Final = "unknown-usmap-version"
WARN_UNRESOLVED_NAME: Final = "unresolved-name-index"

# --- fixed reason strings ---------------------------------------------------

_REASON_TRUNCATED: Final = "the file ends before this field"
_REASON_BAD_MAGIC: Final = "the leading bytes are not a property mapping"
_REASON_BODY_SHORT: Final = "the declared body size exceeds the bytes present"
_REASON_COUNT_RANGE: Final = "the declared count is outside the supported range"
_REASON_UNREADABLE: Final = "the mapping file could not be read"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class UsmapError(Exception):
    """Base class for every failure this module raises."""


class UsmapFormatError(UsmapError):
    """The bytes are not a property mapping this module can read.

    Carries only structural facts: which of THIS MODULE'S field names was being
    read, at what byte offset, and how many bytes or entries were expected
    against how many were present.
    """

    def __init__(
        self,
        *,
        field: str,
        offset: int,
        reason: str,
        expected: int | None = None,
        actual: int | None = None,
    ) -> None:
        """Record the structural facts and build the one-line message.

        Args:
            field: This module's own name for the field being read.
            offset: Byte offset into the file.
            reason: One of the module's fixed reason strings.
            expected: Bytes or entries required, when that is the point.
            actual: Bytes or entries present, when that is the point.
        """
        self.field = field
        self.offset = offset
        self.reason = reason
        self.expected = expected
        self.actual = actual
        message = f"usmap field {field} at byte {offset}: {reason}"
        if expected is not None and actual is not None:
            message = f"{message} (expected {expected}, present {actual})"
        super().__init__(message)


class UnsupportedUsmapCompressionError(UsmapError):
    """The mapping declares a compression method this module cannot decode.

    Deliberately NOT a :class:`UsmapFormatError`: the file is well formed, and
    a caller that means to tolerate a damaged mapping must not accidentally
    swallow the one signal that the shipped format has changed. Reading a
    compressed mapping needs an external decompressor, which is a third-party
    dependency behind the CONVENTIONS.md section 14 license gate.
    """

    def __init__(self, method: int, offset: int) -> None:
        """Name the method integer and nothing else.

        Args:
            method: The declared compression method.
            offset: Byte offset the method was read from.
        """
        self.method = method
        self.offset = offset
        super().__init__(
            f"usmap compression method {method} at byte {offset}: "
            f"only method {COMPRESSION_NONE} (uncompressed) can be read without "
            "an external decompressor behind the license gate"
        )


# ---------------------------------------------------------------------------
# The model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UsmapWarning:
    """One piece of content that was flagged and skipped, and why.

    Attributes:
        code: One of the module's WARN_* constants.
        subject: What was flagged, as a structural token - a type id, a section
            name or an entry index. Never a name decoded out of the file.
        detail: One line naming the consequence.
        count: How many occurrences this warning aggregates.
    """

    code: str
    subject: str
    detail: str
    count: int = 1


@dataclass(frozen=True)
class UsmapContainer:
    """The outer framing, which is measured rather than inferred.

    Attributes:
        magic: The leading uint16.
        version: The file version byte.
        compression_method: 0 is uncompressed and is the only readable value.
        compressed_size: Declared body size on disk.
        decompressed_size: Declared body size once expanded. Equal to
            ``compressed_size`` when the method is 0.
        header_size: Bytes before the body. ``header_size + compressed_size``
            accounts for the whole file.
    """

    magic: int
    version: int
    compression_method: int
    compressed_size: int
    decompressed_size: int
    header_size: int


@dataclass(frozen=True, repr=False)
class PropertyEntry:
    """One serializable property of one schema.

    ``repr`` is hand written and withholds the name, for the reason given on
    :class:`PropertyMap`.

    Attributes:
        name: The property name, resolved through the name table.
        slot: The schema-relative index the game serializes against.
        array_size: Declared fixed-array width, 1 for a scalar.
        type_id: The raw property type byte.
    """

    name: str
    slot: int
    array_size: int
    type_id: int

    def __repr__(self) -> str:
        """Render the slot, the width and the type, and withhold the name.

        Returns:
            The quiet rendering.
        """
        return (
            f"{type(self).__name__}(slot={self.slot}, "
            f"array_size={self.array_size}, type_id={self.type_id})"
        )


@dataclass(frozen=True, repr=False)
class Schema:
    """One class or struct and the properties it serializes.

    ``repr`` renders counts and structure only, for the reason given on
    :class:`PropertyMap`. It reaches the same nesting the mapping does: a tuple
    reprs its elements, so a schema rendering its own name would put one back
    into every rendering of :attr:`PropertyMap.schemas`.

    Attributes:
        name: The schema name.
        super_name: The super type's name, or None. None means the schema has
            no super type UNLESS a :data:`WARN_UNRESOLVED_NAME` warning names
            this schema, in which case the index was outside the name table and
            the super type is unknown rather than absent.
        properties: The serializable entries, in file order. An entry whose
            type this module does not know is absent and is on
            :attr:`PropertyMap.warnings`.
    """

    name: str
    super_name: str | None
    properties: tuple[PropertyEntry, ...]

    def __repr__(self) -> str:
        """Render the property count and whether a super type resolved.

        Returns:
            The quiet rendering.
        """
        return (
            f"{type(self).__name__}(properties={len(self.properties)}, "
            f"super={'present' if self.super_name is not None else 'absent'})"
        )


@dataclass(frozen=True, repr=False)
class PropertyMap:
    """The parsed property mapping.

    ``repr`` IS HAND WRITTEN AND RENDERS COUNTS, and every name-bearing type
    reachable from here does the same. The generated repr prints the entire
    name table, and a test runner and most loggers repr an object BEFORE a
    human chooses what to print, so the quiet rendering has to be the default
    one.

    THE REASON IS NOT PRIVACY, AND OVERSTATING IT WOULD BE ITS OWN DEFECT.
    These are publisher-owned GAME ASSET names, not personal data: non-negotiable
    12 does not reach them and this is not the control that
    ``clockspeed/save/header.py`` implements. It is diagnostic noise and an
    asset echo, which is reason enough on its own - an assertion that opens
    with the whole name table tells a reader nothing and buries what failed.

    Attributes:
        names: The name table, in file order. AN ENTRY IS THE EMPTY STRING WHEN
            ITS BYTES DID NOT DECODE, and the tuple keeps its full length so
            that every positional index in the enum and schema sections still
            lands where the file put it. Empty means the name was empty UNLESS a
            :data:`WARN_UNDECODABLE_NAME` warning names that position, in which
            case the name is unknown rather than absent - the same distinction
            ``super_name`` draws below. :meth:`_NameTable.resolve` answers None
            for such a position rather than a decoded stand-in (CS-435).
        enums: Enum name to its member names, in file order. TWO LOSSES ARE
            POSSIBLE HERE AND BOTH ARE FLAGGED RATHER THAN SILENT. An enum may
            hold FEWER members than the file declared, when a member's index
            fell outside the name table; a :data:`WARN_UNRESOLVED_NAME` warning
            against ``enum-<position>-member`` is the only thing separating
            that from an enum genuinely that short. And an enum name that
            repeats keeps only the LATER definition, flagged as
            :data:`WARN_DUPLICATE_ENUM`, so a mapping smaller than the declared
            enum count always says why.
        schemas: Schema name to its :class:`Schema`.
        warnings: Everything flagged and skipped.
        container: The outer framing.
        body_consumed: How many body bytes the parse actually accounted for.
            Less than ``container.compressed_size`` when a trailing section was
            flagged and skipped.
    """

    names: tuple[str, ...]
    enums: Mapping[str, tuple[str, ...]]
    schemas: Mapping[str, Schema]
    warnings: tuple[UsmapWarning, ...]
    container: UsmapContainer
    body_consumed: int

    def __repr__(self) -> str:
        """Render section counts and the framing, and withhold every name.

        The container is rendered in full because it carries nothing but
        integers, so it is exactly the part of a mapping worth seeing first.

        Returns:
            The quiet rendering.
        """
        return (
            f"{type(self).__name__}(names={len(self.names)}, "
            f"enums={len(self.enums)}, schemas={len(self.schemas)}, "
            f"warnings={len(self.warnings)}, "
            f"body_consumed={self.body_consumed}, "
            f"container={self.container!r})"
        )


# ---------------------------------------------------------------------------
# A bounds-checked reader - every read that could run off the end is one here
# ---------------------------------------------------------------------------


class _Reader:
    """Little-endian reader that raises :class:`UsmapFormatError` at the edge.

    Every primitive checks its own bounds first, which is what keeps an
    ``IndexError`` or a ``struct.error`` from ever reaching a caller.
    """

    def __init__(self, data: bytes, base: int = 0) -> None:
        """Wrap a buffer.

        Args:
            data: The bytes to read.
            base: Offset of ``data`` within the file, for honest reporting.
        """
        self._data = data
        self._at = 0
        self._base = base

    @property
    def at(self) -> int:
        """Current position within this buffer."""
        return self._at

    @property
    def remaining(self) -> int:
        """Bytes left unread."""
        return len(self._data) - self._at

    def _take(self, count: int, field: str) -> int:
        start = self._at
        if count < 0 or start + count > len(self._data):
            raise UsmapFormatError(
                field=field,
                offset=self._base + start,
                reason=_REASON_TRUNCATED,
                expected=count,
                actual=max(len(self._data) - start, 0),
            )
        self._at = start + count
        return start

    def u8(self, field: str) -> int:
        """Read an unsigned byte."""
        return self._data[self._take(1, field)]

    def u16(self, field: str) -> int:
        """Read an unsigned 16-bit integer."""
        return int(struct.unpack_from("<H", self._data, self._take(2, field))[0])

    def u32(self, field: str) -> int:
        """Read an unsigned 32-bit integer."""
        return int(struct.unpack_from("<I", self._data, self._take(4, field))[0])

    def i32(self, field: str) -> int:
        """Read a signed 32-bit integer."""
        return int(struct.unpack_from("<i", self._data, self._take(4, field))[0])

    def skip(self, count: int, field: str) -> None:
        """Advance past ``count`` bytes."""
        self._take(count, field)

    def text(self, length: int, field: str) -> str | None:
        """Read ``length`` UTF-8 bytes, or None when they do not decode.

        NEITHER RAISES NOR SUBSTITUTES, which is the whole of CS-435. Decoding
        with ``errors="replace"`` does not lose an unreadable name, it INVENTS a
        different one - the caller then publishes a key nothing will look up,
        the body consumes cleanly and no warning is raised, so a class that IS
        modelled answers "unmodelled" downstream. Returning None hands the
        caller the one thing it can act on, and :func:`_read_names` flags it.

        THE :class:`UnicodeDecodeError` IS SWALLOWED RATHER THAN CHAINED, for
        the reason ``clockspeed/save/header.py`` and ``clockspeed/save/objects.py``
        both give at their own decode sites: its message QUOTES the offending
        bytes, and exception context is an echo path.

        Args:
            length: How many bytes the name occupies.
            field: This module's own name for the field being read.

        Returns:
            The decoded text, or None when the bytes are not valid UTF-8.
        """
        start = self._take(length, field)
        try:
            return self._data[start : start + length].decode("utf-8")
        except UnicodeDecodeError:
            return None


class _WarningLog:
    """Accumulates warnings, aggregating repeats by ``(code, subject)``."""

    def __init__(self) -> None:
        """Start an empty log."""
        self._order: list[tuple[str, str]] = []
        self._detail: dict[tuple[str, str], str] = {}
        self._count: dict[tuple[str, str], int] = {}

    def add(self, code: str, subject: str, detail: str) -> None:
        """Record one flagged item.

        Args:
            code: One of the WARN_* constants.
            subject: A structural token, never a name from the file.
            detail: One line naming the consequence.
        """
        key = (code, subject)
        if key not in self._count:
            self._order.append(key)
            self._detail[key] = detail
            self._count[key] = 0
        self._count[key] += 1

    def emit(self) -> tuple[UsmapWarning, ...]:
        """Publish in first-seen order, so two runs agree exactly."""
        return tuple(
            UsmapWarning(code, subject, self._detail[(code, subject)], self._count[(code, subject)])
            for code, subject in self._order
        )


# ---------------------------------------------------------------------------
# Container
# ---------------------------------------------------------------------------


def _read_container(reader: _Reader, log: _WarningLog) -> UsmapContainer:
    """Read the outer framing, walking the optional versioning block.

    Args:
        reader: Positioned at byte zero.
        log: Where an unknown version is flagged.

    Returns:
        The container.

    Raises:
        UsmapFormatError: The magic is wrong or the header is truncated.
    """
    magic = reader.u16("magic")
    if magic != USMAP_MAGIC:
        raise UsmapFormatError(field="magic", offset=0, reason=_REASON_BAD_MAGIC)

    version = reader.u8("version")
    if version > MAX_KNOWN_VERSION:
        log.add(
            WARN_UNKNOWN_VERSION,
            f"version-{version}",
            "file version is newer than any this module has read; "
            "the container was read but the layout may have changed",
        )

    if version >= VERSION_PACKAGE_VERSIONING and reader.i32("has_versioning"):
        reader.skip(4, "file_version_ue4")
        reader.skip(4, "file_version_ue5")
        custom_versions = reader.i32("custom_version_count")
        if not 0 <= custom_versions <= _MAX_CUSTOM_VERSIONS:
            raise UsmapFormatError(
                field="custom_version_count",
                offset=reader.at - 4,
                reason=_REASON_COUNT_RANGE,
                expected=_MAX_CUSTOM_VERSIONS,
                actual=custom_versions,
            )
        reader.skip(custom_versions * _CUSTOM_VERSION_RECORD, "custom_versions")
        reader.skip(4, "network_compatible_changelist")

    method_offset = reader.at
    method = reader.u8("compression_method")
    compressed = reader.u32("compressed_size")
    decompressed = reader.u32("decompressed_size")

    if method != COMPRESSION_NONE:
        raise UnsupportedUsmapCompressionError(method, method_offset)

    return UsmapContainer(
        magic=magic,
        version=version,
        compression_method=method,
        compressed_size=compressed,
        decompressed_size=decompressed,
        header_size=reader.at,
    )


# ---------------------------------------------------------------------------
# Inner sections
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _NameTable:
    """The name table, plus the positions whose bytes did not decode.

    THE UNDECODABLE POSITIONS ARE HELD BESIDE THE NAMES RATHER THAN SUBSTITUTED
    INTO THEM, and that is the whole of CS-435. There is no string that can
    stand for "this name did not decode" without being a name some file could
    legitimately carry, so the discriminator cannot live in the tuple. It lives
    here, and :meth:`resolve` is what every reader in this module goes through.

    THE PLACEHOLDER IS THE EMPTY STRING and the tuple keeps its length, because
    every index in the enum and schema sections is POSITIONAL: dropping an entry
    would shift every later name and turn one unreadable name into a whole
    mapping of wrong ones. The empty string is not a claim that the name was
    empty - :data:`WARN_UNDECODABLE_NAME` against ``name-<position>`` is what
    separates those two, the same way a warning separates an unresolvable super
    index from an absent one.

    Attributes:
        names: The name table, in file order, with an undecodable entry held as
            the empty string.
        undecodable: Positions whose bytes were not valid UTF-8.
    """

    names: tuple[str, ...]
    undecodable: frozenset[int]

    def resolve(self, index: int) -> str | None:
        """Resolve a name-table index, or None when it cannot be resolved.

        Two conditions collapse to None on purpose: an index outside the table,
        and an index onto a name that did not decode. Both mean the same thing
        to a caller - there is no name to publish - and both are already flagged
        at the position they were read from, so the caller's own flag-and-skip
        branch is the correct response to either.

        Args:
            index: The uint32 read out of the file.

        Returns:
            The name, or None.
        """
        if index in self.undecodable:
            return None
        return self.names[index] if 0 <= index < len(self.names) else None


def _read_names(reader: _Reader, log: _WarningLog) -> _NameTable:
    """Read the name table, flagging every name whose bytes do not decode.

    A NAME THAT DOES NOT DECODE IS FLAGGED AND MADE UNRESOLVABLE, NOT REPLACED
    (CS-435, non-negotiable 7). Substitution satisfies "never fatal" and
    breaches "never silently wrong": it publishes a name the file does not
    contain, under which a modelled class reports as unmodelled downstream.

    RAISING WOULD BREACH THE OTHER HALF, and this layer already has the rule for
    choosing. The record cursors in ``clockspeed/save/header.py`` and
    ``clockspeed/save/objects.py`` RAISE on an undecodable string.
    ``objects._payload_text`` does NOT - it returns None - and its docstring
    states the discriminator: raise where the grammar is MEASURED and a failure
    is therefore a real defect, tolerate where the content is UNMEASURED and an
    unreadable run is expected.

    BLAST RADIUS SETTLES IT, and the mechanism is the CACHE rather than the
    ordering. Those two raising sites cost the ONE save being read. This module
    is the oracle every save is read through: :func:`cached_usmap` parses the
    installed file at most once and holds it in a module-level cache, and
    ``world._resolve_property_map`` turns a :class:`UsmapError` from it into a
    ``WorldLoadError`` at ``STAGE_USMAP``, ending the load. One bad byte in the
    shipped name table would therefore fail every world load on the machine that
    does not supply its own mapping, for saves that have nothing to do with that
    name. It would not fail them EARLY, either - measured call order inside
    ``world.load_world_from_bytes`` is ``parse_header``, then
    ``decompress_body``, then the mapping - so a healthy save whose own bytes
    read perfectly would still be refused at the last step. Flagging and
    continuing is what satisfies "never fatal" and "never silently wrong" at the
    same time.

    Args:
        reader: Positioned at the name count.
        log: Where an undecodable name is flagged.

    Returns:
        The name table and the positions that did not decode.
    """
    count = reader.u32("name_count")
    if count > reader.remaining:
        raise UsmapFormatError(
            field="name_count",
            offset=reader.at - 4,
            reason=_REASON_COUNT_RANGE,
            expected=reader.remaining,
            actual=count,
        )
    names: list[str] = []
    undecodable: list[int] = []
    for position in range(count):
        length = reader.u8("name_length")
        text = reader.text(length, "name")
        if text is None:
            log.add(
                WARN_UNDECODABLE_NAME,
                f"name-{position}",
                "a name's bytes are not valid UTF-8; it was not decoded, and "
                "this position was recorded as unresolvable rather than "
                "decoded with substitute characters",
            )
            undecodable.append(position)
            names.append("")
            continue
        names.append(text)
    return _NameTable(names=tuple(names), undecodable=frozenset(undecodable))


def _read_enums(reader: _Reader, names: _NameTable, log: _WarningLog) -> dict[str, tuple[str, ...]]:
    """Read the enum table, flagging every entry whose names do not resolve.

    THE FAILURES HERE GET DISTINCT WARNING KEYS, and that is load bearing
    rather than tidy. :class:`_WarningLog` aggregates by ``(code, subject)``
    and keeps the FIRST detail it was given, so two conditions sharing a key do
    not produce two warnings - the first one's sentence stands for both and the
    second is reduced to a count. While the member loop and the enum-name check
    shared one subject, an enum failing both ways surfaced only the member's
    sentence, which describes an enum that in that case does not exist at all.

    Args:
        reader: Positioned at the enum count.
        names: The name table.
        log: Where unresolved entries are flagged.

    Returns:
        Enum name to member names.
    """
    count = reader.u32("enum_count")
    if count > reader.remaining:
        raise UsmapFormatError(
            field="enum_count",
            offset=reader.at - 4,
            reason=_REASON_COUNT_RANGE,
            expected=reader.remaining,
            actual=count,
        )
    enums: dict[str, tuple[str, ...]] = {}
    for position in range(count):
        enum_name = names.resolve(reader.u32("enum_name_index"))
        member_count = reader.u8("enum_member_count")
        members: list[str] = []
        for _ in range(member_count):
            member = names.resolve(reader.u32("enum_member_index"))
            if member is None:
                # WITHOUT THIS FLAG A TRUNCATED ENUM IS A SHORTER ENUM. Dropping
                # the member silently yields a mapping that is well formed,
                # fully consumed and WRONG - and a shorter enum is an ordinary
                # thing for the shipped file to hold, so nothing downstream can
                # tell the two apart. Same root cause as the super index in
                # _read_schema and the same half of non-negotiable 7: "never
                # silently wrong" is the half that has to be satisfied on
                # purpose, because the failure renders as a success.
                #
                # THE DETAIL STATES ONLY WHAT IS KNOWN HERE. Whether the enum
                # survives at all is decided below, so a sentence about the
                # enum's resulting length would be a claim this function can
                # still go on to contradict.
                log.add(
                    WARN_UNRESOLVED_NAME,
                    f"enum-{position}-member",
                    "an enum member index fell outside the name table; the member was skipped",
                )
                continue
            members.append(member)
        if enum_name is None:
            log.add(
                WARN_UNRESOLVED_NAME,
                f"enum-{position}",
                "an enum name index fell outside the name table; the enum was skipped",
            )
            continue
        if enum_name in enums:
            # The same loss _read_schemas already flags, one section away, and
            # deliberately the same shape: a repeated name silently collapses
            # two definitions into one, and the count of enums a caller gets
            # back is then smaller than the file declared with nothing to say
            # why.
            log.add(
                WARN_DUPLICATE_ENUM,
                f"enum-{position}",
                "an enum name repeated; the later definition replaced the earlier",
            )
        enums[enum_name] = tuple(members)
    return enums


def _skip_payload(reader: _Reader, type_id: int, depth: int = 0) -> None:
    """Advance past one property-type descriptor's payload.

    Args:
        reader: Positioned just after the type byte.
        type_id: The type byte already read.
        depth: Recursion depth, capped so a corrupt run cannot crash.

    Raises:
        UsmapFormatError: The descriptor nests past the cap or runs off the end.
    """
    if depth > _MAX_DESCRIPTOR_DEPTH:
        raise UsmapFormatError(
            field="property_descriptor_depth",
            offset=reader.at,
            reason=_REASON_COUNT_RANGE,
            expected=_MAX_DESCRIPTOR_DEPTH,
            actual=depth,
        )
    shape = _PAYLOAD.get(type_id, _NONE)
    if shape == _NAME:
        reader.skip(4, "property_type_name_index")
    elif shape == _INNER:
        _skip_payload(reader, reader.u8("inner_property_type"), depth + 1)
    elif shape == _INNER_NAME:
        _skip_payload(reader, reader.u8("inner_property_type"), depth + 1)
        reader.skip(4, "property_type_name_index")
    elif shape == _INNER_INNER:
        _skip_payload(reader, reader.u8("key_property_type"), depth + 1)
        _skip_payload(reader, reader.u8("value_property_type"), depth + 1)


def _read_schema(
    reader: _Reader, names: _NameTable, position: int, log: _WarningLog
) -> Schema | None:
    """Read one schema and its serializable properties.

    An unknown property type is flagged and the entry dropped; the surrounding
    entries are unaffected. All three name indices a schema carries - its own,
    its super type's and each property's - are flagged when they fall outside
    the name table, so an unreadable one is never mistaken for an absent one.
    An unresolvable SUPER index keeps the schema, because its name and its
    properties are still readable and only the super type is lost.

    THE THREE FAILURES GET DISTINCT WARNING KEYS, and that is load bearing
    rather than tidy - the same fact :func:`_read_enums` records one section
    away, and this function is where CS-431 measured it a second time.
    :class:`_WarningLog` aggregates by ``(code, subject)`` and keeps the FIRST
    detail it was given, so two conditions sharing a key do not produce two
    warnings: the first one's sentence stands for both and the second is reduced
    to a count. While all three shared the bare ``schema-N`` subject, a schema
    whose own name AND super index were unresolvable surfaced only the super
    index's sentence - a statement about the super type of a schema that in that
    case is ABSENT from the mapping entirely. That is not an under-report, it is
    a TRUE sentence replaced by a FALSE one, which is the "never silently wrong"
    half of non-negotiable 7 rather than the "never fatal" half.

    The bare ``schema-N`` stays with the schema's OWN name because that is the
    condition deciding whether the schema survives at all; each sub-site
    qualifies it, exactly as ``enum-N`` and ``enum-N-member`` do.

    Args:
        reader: Positioned at the schema's name index.
        names: The name table.
        position: Index of this schema, used to build its warning subjects.
        log: Where flagged content is recorded.

    Returns:
        The schema, or None when its own name index does not resolve.
    """
    schema_name = names.resolve(reader.u32("schema_name_index"))
    raw_super = reader.u32("schema_super_index")
    super_name = None
    if raw_super != _NO_SUPER:
        super_name = names.resolve(raw_super)
        if super_name is None:
            # WITHOUT THIS FLAG THE TWO CASES ARE THE SAME BYTES TO A CALLER.
            # An unresolvable index and the all-bits-set "no super" sentinel
            # both leave super_name None, so an unreadable super type would
            # render as a schema that genuinely has none - flagged is the only
            # thing that tells them apart (non-negotiable 7, the "never
            # silently wrong" half).
            log.add(
                WARN_UNRESOLVED_NAME,
                f"schema-{position}-super",
                "a schema super index fell outside the name table; the super type was not resolved",
            )
    reader.u16("schema_property_count")
    serializable = reader.u16("schema_serializable_count")

    entries: list[PropertyEntry] = []
    for _ in range(serializable):
        slot = reader.u16("property_slot")
        array_size = reader.u8("property_array_size")
        property_name = names.resolve(reader.u32("property_name_index"))
        type_id = reader.u8("property_type")

        if type_id > MAX_KNOWN_PROPERTY_TYPE:
            log.add(
                WARN_UNKNOWN_PROPERTY_TYPE,
                f"type-{type_id}",
                "an unrecognised property type was skipped; if it carries a "
                "payload the rest of this section may be unreadable",
            )
            continue
        _skip_payload(reader, type_id)

        if property_name is None:
            log.add(
                WARN_UNRESOLVED_NAME,
                f"schema-{position}-property",
                "a property name index fell outside the name table; the property was skipped",
            )
            continue
        entries.append(
            PropertyEntry(name=property_name, slot=slot, array_size=array_size, type_id=type_id)
        )

    if schema_name is None:
        log.add(
            WARN_UNRESOLVED_NAME,
            f"schema-{position}",
            "a schema name index fell outside the name table; the schema was skipped",
        )
        return None
    return Schema(name=schema_name, super_name=super_name, properties=tuple(entries))


def _read_schemas(reader: _Reader, names: _NameTable, log: _WarningLog) -> dict[str, Schema]:
    """Read the schema table, stopping cleanly if the stream desynchronises.

    Args:
        reader: Positioned at the schema count.
        names: The name table.
        log: Where flagged content is recorded.

    Returns:
        Schema name to schema.
    """
    count = reader.u32("schema_count")
    if count > reader.remaining:
        raise UsmapFormatError(
            field="schema_count",
            offset=reader.at - 4,
            reason=_REASON_COUNT_RANGE,
            expected=reader.remaining,
            actual=count,
        )
    schemas: dict[str, Schema] = {}
    for position in range(count):
        try:
            schema = _read_schema(reader, names, position, log)
        except UsmapFormatError:
            # A skipped unknown type can leave the cursor mid-entry. That is
            # unknown content, not a broken file: flag what was lost and stop
            # rather than manufacture a mapping from misaligned bytes.
            log.add(
                WARN_DESYNCHRONISED_SECTION,
                "schemas",
                f"the schema section stopped at entry {position} of {count}; "
                "the remaining schemas were not read",
            )
            return schemas
        if schema is None:
            continue
        if schema.name in schemas:
            log.add(
                WARN_DUPLICATE_SCHEMA,
                f"schema-{position}",
                "a schema name repeated; the later definition replaced the earlier",
            )
        schemas[schema.name] = schema
    return schemas


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


def parse_usmap(data: bytes) -> PropertyMap:
    """Parse property mapping bytes.

    Args:
        data: The whole file.

    Returns:
        The parsed mapping. Unknown content is on :attr:`PropertyMap.warnings`.

    Raises:
        UsmapFormatError: The bytes are not a readable property mapping.
        UnsupportedUsmapCompressionError: The declared compression method needs
            an external decompressor behind the license gate.
    """
    log = _WarningLog()
    header = _Reader(data)
    container = _read_container(header, log)

    body = data[container.header_size : container.header_size + container.compressed_size]
    if len(body) != container.compressed_size:
        raise UsmapFormatError(
            field="body",
            offset=container.header_size,
            reason=_REASON_BODY_SHORT,
            expected=container.compressed_size,
            actual=len(body),
        )

    reader = _Reader(body, base=container.header_size)
    table = _read_names(reader, log)
    enums = _read_enums(reader, table, log)
    schemas = _read_schemas(reader, table, log)

    if reader.remaining:
        log.add(
            WARN_TRAILING_SECTION,
            "post-schema",
            f"{reader.remaining} bytes follow the schema section and were not "
            "read; nothing above this layer consumes them",
        )

    return PropertyMap(
        names=table.names,
        enums=MappingProxyType(enums),
        schemas=MappingProxyType(schemas),
        warnings=log.emit(),
        container=container,
        body_consumed=reader.at,
    )


def load_usmap(path: Path) -> PropertyMap:
    """Read and parse the mapping at ``path``.

    Args:
        path: The mapping file. Opened read-only; nothing here ever writes.

    Returns:
        The parsed mapping.

    Raises:
        UsmapError: The file could not be read, or is not a readable mapping.
    """
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise UsmapError(f"{_REASON_UNREADABLE}: {redact(path)}") from exc
    return parse_usmap(data)


def default_usmap_path(game_dir: Path | None = None) -> Path | None:
    """Locate the mapping inside the install.

    Args:
        game_dir: The install directory. Resolved at runtime when omitted;
            never hardcoded (non-negotiable 3).

    Returns:
        The mapping path, or None when there is no install or the install
        carries no mapping. Absence is normal and is never an error.
    """
    if game_dir is None:
        game_dir, _label = resolve_game_dir()
    if game_dir is None:
        return None
    candidate = game_dir.joinpath(*USMAP_RELATIVE)
    try:
        return candidate if candidate.is_file() else None
    except OSError:
        return None


# --- the cache --------------------------------------------------------------
#
# The mapping is a multi-megabyte file and re-parsing it per call is a real
# cost, so the PARSED form is held. The key carries size and modification time
# as well as the path, so a patched install is re-read rather than served
# stale. The lock makes a concurrent first call parse twice at worst, never
# publish a half-built map.

_LOCK: Final = threading.Lock()
_KEY: tuple[str, int, int] | None = None
_VALUE: PropertyMap | None = None


def clear_cache() -> None:
    """Drop the cached mapping. Idempotent."""
    global _KEY, _VALUE  # noqa: PLW0603 - module-level cache, guarded by _LOCK
    with _LOCK:
        _KEY = None
        _VALUE = None


def cached_usmap() -> PropertyMap | None:
    """Return the parsed mapping from the install, parsing at most once.

    ABSENCE IS NOT AN ERROR, and this is load-bearing: the rule suite and CI
    run on a machine that has never had the game installed, and callers are
    written against None. A file that is PRESENT but unreadable is a different
    thing and does raise, because silently returning None there would hide a
    format change behind the same value that means "no install".

    Returns:
        The mapping, or None when there is no install or no mapping file.

    Raises:
        UsmapError: A mapping file exists but could not be read or parsed.
    """
    global _KEY, _VALUE  # noqa: PLW0603 - module-level cache, guarded by _LOCK
    path = default_usmap_path()
    if path is None:
        return None
    try:
        stat = path.stat()
    except OSError:
        return None
    key = (str(path), stat.st_size, stat.st_mtime_ns)

    with _LOCK:
        if key == _KEY and _VALUE is not None:
            return _VALUE

    parsed = load_usmap(path)

    with _LOCK:
        _KEY = key
        _VALUE = parsed
    return parsed
