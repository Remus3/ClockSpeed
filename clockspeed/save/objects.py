"""The object-header walk, and property resolution against the property mapping.

WHAT THIS MODULE OWNS
-----------------------
The decompressed body's leading length prefix, the object record table, the
version-dispatched transform block, and the rule ``docs/ARCHITECTURE.md``
assigns here: **an unknown actor class is logged and SKIPPED, never fatal.**

It takes bytes plus two version scalars. It does not read the header itself, it
does not walk chunks, and it opens no file - so it can be written and tested
beside its neighbours, and ADR 0007 decision item 6 (``workdir.py`` is the only
writer in this package) stays trivially true here.

TWO DISPATCHES, AND THEY ARE INDEPENDENT
------------------------------------------
This is the single most important property in the module, and a parser that
gets it wrong passes almost every fixture.

- The **body length prefix width** follows the HEADER version: an int64 on
  header versions 13 and 14, an int32 on header version 10. Corrected under
  CS-404 this session - an earlier record had the prefix ABSENT on header 10,
  which was a property of one fixture rather than of the format.
- The **transform delta** - the filler between the instance-name string and the
  transform block - follows the SAVE version: 4 on save 36, 8 on saves 52 and
  60, per ADR 0003, which measured 626 node actors with 626 valid transforms.

Across the whole real library the two covary: header 10 always appears with
save 36, header 14 with saves 52 and 60. So a parser reading both decisions off
one field is correct on every real file and on every real-shaped fixture. The
corpus therefore carries ``SAVE_CROSS`` - header 14 with save 36, a combination
in no real file - whose measured pair is (8, 4). It is the only thing that
separates the two dispatches, and it is why they are looked up through two
functions here rather than through one.

SAVE VERSION 42 IS DELIBERATELY ABSENT FROM THE DELTA TABLE
-------------------------------------------------------------
Its delta has never been measured. With 36 -> 4 beside 52 -> 8, a value of 4 or
6 for 42 looks derived rather than invented, which is exactly what makes it
dangerous: every input to the interpolation is a genuine measurement, and the
output is not. ADR 0005 records the same failure shape for the overclock
exponent and refuses it there for the same reason. An absent key RAISES
:class:`UnsupportedSaveVersionError`; it never defaults.

The refusal is EAGER, before a single record is read, matching ``header.py``'s
version prologue. A check placed after the walk would never fire on a save of
an unmeasured version whose object table happens to be empty, and would fire
only once a populated one arrived - a version-dependent time bomb rather than a
version check.

UNKNOWN CLASSES ARE THE RELEASE VALVE (non-negotiable 7, BOOTSTRAP.md section 9)
---------------------------------------------------------------------------------
A class path the supplied registry does not model is recorded in
:attr:`ObjectTable.unknown_classes` with a count and a fixed reason, its
property payload is skipped, and **the walk continues to the end of the
table**. :attr:`ObjectTable.contains_unmodeled_content` then reports that the
world holds content this project does not model. Partial coverage is a flagged,
visible state - never a failure and never a silently wrong number. That single
decision is what makes mod tolerance nearly free: a namespaced ``/Mods/`` path
takes the ordinary route and no mod-specific branch exists.

A registry is OPTIONAL, and its absence claims nothing. ``cached_usmap()``
returns None on a machine with no install, and a walk that responded by
flagging every class would report a world of pure unknown content rather than a
world it has not checked. ``known_classes=None`` therefore flags nothing.

WHAT IS MEASURED HERE AND WHAT IS NOT, STATED PLAINLY
-------------------------------------------------------
Measured, and exercised by the corpus: the prefix widths, the record table
grammar for an actor, and the transform deltas for save versions 36, 52 and 60.

NOT measured, and deliberately not invented:

0. **Where the record table actually STARTS in a real body.** This module walks
   the table from the first byte after the length prefix, which is the layout
   ``tests/save/synthetic.py`` builds - and that corpus labels its own body
   layout MODELLED rather than measured. A probe run against all four real
   version pairs this session shows the assumption does NOT hold on a real
   save: the first int32 after the prefix is 201 on header 10 save 36, 6 on
   header 13 save 42 and header 14 save 52, and 0 on header 14 save 60, and on
   several of those it is immediately followed by a printable null-terminated
   run rather than by a record. A real body evidently opens with a
   version-dependent preamble that this module does not locate, so
   **the walk below is correct against the corpus and cannot yet read a real
   save.** Locating that preamble is a separate, measured piece of work; it is
   NOT closed by guessing an offset here. The same probe did confirm the
   prefix rule itself against every real pair - declared length equals the body
   length exactly on all four, header 10's int32 included, which is independent
   confirmation of the CS-404 correction.

1. **The object DATA section.** After the record table a real save carries the
   per-object property payloads. No corpus fixture builds one -
   ``SyntheticObject.encode`` emits a header record and stops - so this module
   has never seen the grammar. Bytes remaining after the table are FLAGGED as
   an unparsed section and skipped. :attr:`ObjectRecord.body_offset` and
   :attr:`ObjectRecord.body_length` are the seam that will locate a payload
   once that grammar is measured, and they are 0 on every path today.
2. **The component record grammar.** In the corpus a record encodes identically
   whatever its object-type discriminator says, so this module reads one
   grammar and takes ``kind`` from the discriminator. A real save's component
   header is believed to carry an outer/parent path where an actor carries a
   transform; nothing here has measured that, so :attr:`ObjectRecord.parent` is
   None on every path and the component branch is UNVERIFIED against a real
   file.
3. **Property VALUE decoding.** :func:`read_properties` resolves a class path to
   a usmap schema and reports whether the mapping models it. It decodes no
   value, because the payload grammar is unmeasured. A payload with a non-zero
   extent is flagged as unparsed rather than guessed at.

An unrecognised object-type discriminator is refused rather than skipped, and
that is not a contradiction of non-negotiable 7. That rule covers unknown
CONTENT - a class this project does not model - which can be flagged and
stepped over because the record around it is still readable. A record whose
GRAMMAR is unknown carries no length, so there is nothing to step over and no
way to resume; guessing the actor grammar for it would desynchronise the rest
of the table silently.

THE ERROR TAXONOMY IS A PRIVACY CONTROL, NOT A STYLE
------------------------------------------------------
A save BODY is personal-data-bearing: it holds the world's contents and its
actor names. Non-negotiable 12 therefore makes every exception an echo path.
An error raised here may carry ONLY a field name drawn from :data:`FIELD_NAMES`,
a byte offset, an expected/actual length or count, a version scalar and a fixed
``REASON_*`` string. Never raw bytes, never a decoded string, never a hex
preview, never a path - paths go through ``clockspeed.data.locate.redact()``,
and this module never handles one.

The same discipline covers ``__repr__``. :class:`ObjectRecord` and
:class:`ObjectTable` render structure and withhold every string they carry,
because a test runner and most loggers repr an object before a human chooses
what to print, and the safe rendering has to stay safe even when the parse is
wrong.

FLOATS ARE LEGAL HERE, AND NECESSARY
--------------------------------------
Non-negotiable 6 bans floats from the SOLVE path, and the static AST gate's
pinned module set is the solve package. An actor transform is genuinely float32
on the wire; encoding it as anything else would be a reader that lies about the
format.
"""

from __future__ import annotations

import struct
from collections.abc import Container, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from clockspeed.save.usmap import PropertyMap

__all__ = [
    "FIELD_NAMES",
    "KIND_ACTOR",
    "KIND_COMPONENT",
    "MAX_OBJECTS",
    "MAX_STRING_BYTES",
    "MEASURED_HEADER_VERSIONS",
    "TRANSFORM_BYTES",
    "TRANSFORM_DELTA_BY_SAVE_VERSION",
    "TRANSFORM_FLOAT_COUNT",
    "UNKNOWN_CLASS_REASONS",
    "WARN_BODY_LENGTH_DISAGREEMENT",
    "WARN_UNMEASURED_HEADER_VERSION",
    "WARN_UNPARSED_DATA_SECTION",
    "WARN_UNPARSED_PROPERTY_PAYLOAD",
    "WARN_UNRESOLVED_SCHEMA",
    "ObjectBudgetExceededError",
    "ObjectError",
    "ObjectFormatError",
    "ObjectRecord",
    "ObjectTable",
    "ObjectTruncatedError",
    "ObjectWarning",
    "PropertyResult",
    "Transform",
    "UnknownClass",
    "UnsupportedSaveVersionError",
    "class_name_of",
    "parse_object_headers",
    "parse_properties",
    "read_properties",
]

# ---------------------------------------------------------------------------
# Measured layout constants
#
# ADR 0003 owns the transform deltas and ADR 0007 plus BOOTSTRAP.md section 2.4
# own the prefix widths. They are transcribed here rather than imported from
# the test corpus, matching chunks.py: sharing the constant would make the
# suite a restatement of this module's own opinion instead of a check on it.
# tests/save/test_objects.py cross-checks the two transcriptions, which is the
# only evidence that neither slice mistyped the table.
# ---------------------------------------------------------------------------

HEADER_VERSION_10: Final = 10
HEADER_VERSION_13: Final = 13
HEADER_VERSION_14: Final = 14

#: The header versions with a measured body layout. A version outside the set
#: is FLAGGED rather than refused, matching chunks.py: ADR 0007 decision item 3
#: records that the key the framing follows is undetermined, so refusing here
#: would assert a claim the ADR declines to make.
MEASURED_HEADER_VERSIONS: Final = (HEADER_VERSION_10, HEADER_VERSION_13, HEADER_VERSION_14)

#: From this header version the body opens with an int64 length rather than an
#: int32. CORRECTED under CS-404: header 10 carries an int32, not nothing.
HEADER_VERSION_WITH_WIDE_PREFIX: Final = HEADER_VERSION_13

BODY_PREFIX_WIDTH_WIDE: Final = 8
BODY_PREFIX_WIDTH_NARROW: Final = 4

#: MEASURED. The filler width between the instance-name string and the
#: transform block, by SAVE version (ADR 0003).
#:
#: SAVE VERSION 42 IS DELIBERATELY ABSENT - see the module docstring. Adding it
#: is a MEASUREMENT, taken against a real save of that version, and it is
#: added in both transcriptions at once.
TRANSFORM_DELTA_BY_SAVE_VERSION: Final[Mapping[int, int]] = MappingProxyType({36: 4, 52: 8, 60: 8})

#: Rotation (4) + translation (3) + scale (3), all float32.
TRANSFORM_FLOAT_COUNT: Final = 10
TRANSFORM_BYTES: Final = TRANSFORM_FLOAT_COUNT * 4

KIND_ACTOR: Final = "actor"
KIND_COMPONENT: Final = "component"

#: The object-type discriminator values with a measured meaning. Anything else
#: is an unknown GRAMMAR and is refused - see the module docstring.
_KIND_BY_OBJECT_TYPE: Final[Mapping[int, str]] = MappingProxyType(
    {0: KIND_COMPONENT, 1: KIND_ACTOR}
)

INT32_SIZE: Final = 4
INT64_SIZE: Final = 8

#: A negative string count selects UTF-16-LE and its magnitude is a CHARACTER
#: count, so the byte count is twice it. A parser treating the magnitude as
#: bytes reads half the string and lands mid-field.
UTF16_CHAR_SIZE: Final = 2

#: The smallest a record can possibly be, before its save-version delta: the
#: object type, three empty strings at four bytes each, the transform block and
#: the trailing int32. Used to refuse an impossible declared count early.
_MINIMUM_RECORD_BYTES: Final = INT32_SIZE * 5 + TRANSFORM_BYTES

# ---------------------------------------------------------------------------
# Stated resource ceilings
#
# Every one is a REFUSAL BOUND applied to a DECLARED value before any
# allocation. A save is untrusted binary input and an unbounded declared length
# read out of one is the whole attack.
# ---------------------------------------------------------------------------

#: Ceiling on the declared record count. A large built world is a few hundred
#: thousand objects, so this is generous against the measurement and finite.
MAX_OBJECTS: Final = 1 << 20

#: Ceiling on any single declared string length, matching header.py.
MAX_STRING_BYTES: Final = 16_384

# ---------------------------------------------------------------------------
# The closed field vocabulary
#
# The one error parameter allowed to be text. Pinning it to a fixed set means
# no raise site - including one written later - can smuggle a value decoded out
# of the body into a message through it.
# ---------------------------------------------------------------------------

FIELD_NAMES: Final = frozenset(
    {
        "body_length",
        "object_count",
        "object_table",
        "object_type",
        "type_path",
        "root_object",
        "instance_name",
        "transform_delta",
        "transform",
        "was_placed_in_level",
        "save_version",
        "property_payload",
    }
)

# ---------------------------------------------------------------------------
# Fixed reason strings
#
# Every raised message is built from one of these. A test collects them from
# this module and asserts each raised reason is a member, which proves
# mechanically that no decoded body content can reach an exception message.
# ---------------------------------------------------------------------------

REASON_SHORT_BUFFER: Final = "extends past the end of the supplied body"
REASON_DECLARED_LENGTH_ABOVE_CAP: Final = "declares a length above the stated cap"
REASON_NEGATIVE_COUNT: Final = "declares a count below zero, which no table can carry"
REASON_ABOVE_CEILING: Final = "exceeds the stated ceiling for this field"
REASON_UNMEASURED_OBJECT_TYPE: Final = (
    "names an object-type discriminator with no measured record grammar"
)
REASON_UNMEASURED_TRANSFORM_DELTA: Final = (
    "has no measured transform delta, and a delta is never interpolated from its neighbours"
)
REASON_UNDECODABLE_TEXT: Final = "declares text that is not decodable"
REASON_CLASS_NOT_MODELLED: Final = "is not a class the supplied registry models"

#: The reasons a class path can land in :attr:`ObjectTable.unknown_classes`.
UNKNOWN_CLASS_REASONS: Final = frozenset({REASON_CLASS_NOT_MODELLED})

# ---------------------------------------------------------------------------
# Warning codes and their fixed detail lines
# ---------------------------------------------------------------------------

WARN_UNMEASURED_HEADER_VERSION: Final = "unmeasured-header-version"
WARN_BODY_LENGTH_DISAGREEMENT: Final = "body-length-disagreement"
WARN_UNPARSED_DATA_SECTION: Final = "unparsed-data-section"
WARN_UNRESOLVED_SCHEMA: Final = "unresolved-schema"
WARN_UNPARSED_PROPERTY_PAYLOAD: Final = "unparsed-property-payload"

_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_UNMEASURED_HEADER_VERSION: (
            "the header version is outside the measured set, so the body length prefix "
            "width was taken from the nearest measured rule rather than from a measurement"
        ),
        WARN_BODY_LENGTH_DISAGREEMENT: (
            "the body length prefix disagrees with the bytes that follow it; the walk "
            "followed the bytes present rather than the declaration"
        ),
        WARN_UNPARSED_DATA_SECTION: (
            "bytes follow the object record table and were not read; the object data "
            "section grammar is unmeasured and is never guessed at"
        ),
        WARN_UNRESOLVED_SCHEMA: (
            "the class path does not resolve to a schema in the supplied property map, "
            "so its property payload was skipped"
        ),
        WARN_UNPARSED_PROPERTY_PAYLOAD: (
            "the class resolved but its property payload was not decoded; the value "
            "grammar is unmeasured and is never guessed at"
        ),
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
        field: The field at fault, already checked.
        offset: The byte offset.
        expected: An expected length or count.
        actual: An observed or declared length or count.
        version: A version scalar.

    Returns:
        The rendered message.
    """
    parts = [f"save object field {field} at byte {offset} {reason}"]
    if expected is not None:
        parts.append(f"expected {expected}")
    if actual is not None:
        parts.append(f"got {actual}")
    if version is not None:
        parts.append(f"save version {version}")
    return "; ".join(parts)


class ObjectError(Exception):
    """Base class for every refusal this module raises.

    A plain :class:`Exception` rather than a :class:`ValueError`, matching
    ``chunks.py`` and ``clockspeed/data/docs_extract.py``: a caller wrapping a
    broad input handler around a save read should have to name this layer to
    swallow it.

    THE ATTRIBUTE SET IS A PRIVACY CONTROL. Non-negotiable 12 makes an
    exception an echo path for a personal-data-bearing artifact, so an instance
    carries only the five channels below plus the fixed reason, and a test pins
    the set with ``vars(exc)`` rather than trusting review.

    Attributes:
        reason: One of the module's ``REASON_*`` constants. Never built from
            body content.
        field: The field at fault, from :data:`FIELD_NAMES`. A name from this
            module's own vocabulary, never a value read from the body.
        offset: The byte offset the fault was found at.
        expected: An expected length or count, or None.
        actual: A declared or observed length or count, or None.
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
            field: The field at fault, from :data:`FIELD_NAMES`.
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


class ObjectFormatError(ObjectError):
    """A field declared something structurally impossible.

    Distinct from a truncation on purpose. A truncation means the body is
    SHORT; this means the body declares nonsense, and the distinction decides
    whether a caller should suspect a partial write or a wrong format.
    """


class ObjectTruncatedError(ObjectError):
    """The body ended before a field this module needed was complete.

    Every read goes through the bounded cursor, so a truncation arrives here
    rather than as a :class:`struct.error` or an :class:`IndexError` carrying a
    fragment of the buffer.
    """


class ObjectBudgetExceededError(ObjectError):
    """A declared count exceeds a stated ceiling.

    Always raised on the DECLARED value, before the record loop and before any
    list is grown from it.
    """


class UnsupportedSaveVersionError(ObjectError):
    """The save version has no MEASURED transform delta.

    Raised EAGERLY, before any record is read. Interpolating a delta from
    measured neighbours is refused outright - see the module docstring.
    """


# ---------------------------------------------------------------------------
# The models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Transform:
    """One actor's placement, exactly as the wire carries it.

    Float32 is the format's own type here and non-negotiable 6 is scoped to the
    solve path, so these are genuine floats rather than a lossy rendering of
    something else.

    Attributes:
        rotation: The rotation quaternion, in file order.
        translation: World coordinates.
        scale: Per-axis scale.
    """

    rotation: tuple[float, float, float, float]
    translation: tuple[float, float, float]
    scale: tuple[float, float, float]


@dataclass(frozen=True, repr=False)
class ObjectRecord:
    """One entry in the object record table.

    ``repr`` is hand written and withholds every string. A save body holds the
    world's contents and its actor names, and a repr is an echo path under
    non-negotiable 12 just as much as a log line is.

    Attributes:
        kind: :data:`KIND_ACTOR` or :data:`KIND_COMPONENT`, from the
            discriminator. The COMPONENT branch is unverified against a real
            save - see the module docstring.
        type_path: The class path, namespaced and mod tolerant, verbatim.
        root_object: The record's root object path.
        instance_name: The instance name, verbatim.
        transform: The placement. Present whenever the record carried a
            transform block, which in the corpus is every record.
        parent: Reserved for the component grammar's outer path. None on every
            path today, because that grammar is unmeasured.
        object_type: The raw discriminator, carried rather than interpreted.
        was_placed_in_level: The trailing int32, carried verbatim.
        body_offset: Where this object's PROPERTY PAYLOAD begins in the body.
            0 today: the object data section grammar is unmeasured.
        body_length: How many bytes that payload spans. 0 today, same reason.
    """

    kind: str
    type_path: str
    root_object: str
    instance_name: str
    transform: Transform | None
    parent: str | None
    object_type: int
    was_placed_in_level: int
    body_offset: int
    body_length: int

    def __repr__(self) -> str:
        """Render structure and withhold every string.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(kind={self.kind!r}, "
            f"object_type={self.object_type}, "
            f"transform={'present' if self.transform is not None else 'absent'}, "
            f"body_offset={self.body_offset}, body_length={self.body_length})"
        )


@dataclass(frozen=True)
class UnknownClass:
    """One class path the supplied registry does not model.

    Unlike an exception, this IS the reporting channel: naming the class is its
    entire purpose, because BOOTSTRAP.md section 9 requires an explicit "this
    world contains content I do not model" rather than a quiet partial answer.

    Attributes:
        type_path: The unmodelled class path.
        count: How many records carried it. A world with two hundred unmodelled
            belts has one problem, not two hundred.
        reason: One of :data:`UNKNOWN_CLASS_REASONS`.
        first_index: The record index it was first seen at.
    """

    type_path: str
    count: int
    reason: str
    first_index: int


@dataclass(frozen=True)
class ObjectWarning:
    """Something worth reporting that is not worth failing over.

    Attributes:
        code: One of the module's ``WARN_*`` constants.
        detail: A fixed line, keyed by code. Never built from body content.
        offset: The byte offset the condition was noticed at.
        expected: An expected length or count, or None.
        actual: An observed length or count, or None.
    """

    code: str
    detail: str
    offset: int
    expected: int | None = None
    actual: int | None = None


@dataclass(frozen=True, repr=False)
class ObjectTable:
    """The walked record table, and everything noticed on the way.

    ``repr`` renders counts only, for the reason given on :class:`ObjectRecord`.

    Attributes:
        records: Every record, in file order.
        unknown_classes: Class paths the supplied registry did not model,
            aggregated with a count. Empty when no registry was supplied -
            absence of a registry claims nothing.
        warnings: Aggregated advisories, empty when nothing was noticed.
        declared_body_length: The length the body's own prefix declared.
        body_consumed: How many body bytes the record table accounted for.
            Less than ``declared_body_length`` when a data section followed.
        body_prefix_width: 8 on header versions 13 and 14, 4 on header 10.
        transform_delta: The filler width this save version dictates.
        save_version: The save version the walk was dispatched on.
        header_version: The header version the walk was dispatched on.
    """

    records: tuple[ObjectRecord, ...]
    unknown_classes: tuple[UnknownClass, ...]
    warnings: tuple[ObjectWarning, ...]
    declared_body_length: int
    body_consumed: int
    body_prefix_width: int
    transform_delta: int
    save_version: int
    header_version: int

    @property
    def contains_unmodeled_content(self) -> bool:
        """Whether the world holds content this project does not model.

        Returns:
            True when at least one class path went unresolved.
        """
        return bool(self.unknown_classes)

    def __repr__(self) -> str:
        """Render counts and scalars, and withhold every string.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(records={len(self.records)}, "
            f"unknown_classes={len(self.unknown_classes)}, "
            f"warnings={len(self.warnings)}, "
            f"save_version={self.save_version}, header_version={self.header_version}, "
            f"body_prefix_width={self.body_prefix_width}, "
            f"transform_delta={self.transform_delta})"
        )


@dataclass(frozen=True)
class PropertyResult:
    """What :func:`read_properties` could and could not do with one record.

    Attributes:
        properties: The decoded properties. ALWAYS empty today - the value
            grammar is unmeasured and this module never guesses one.
        schema_name: The class name the type path resolved to.
        resolved: Whether the property map models that class at all.
        warnings: What was flagged and skipped.
    """

    properties: Mapping[str, object]
    schema_name: str
    resolved: bool
    warnings: tuple[ObjectWarning, ...]


# ---------------------------------------------------------------------------
# The bounded cursor
# ---------------------------------------------------------------------------


class _Cursor:
    """A bounds-checked forward reader over one body.

    Every read goes through :meth:`_require`, so there is no path that indexes
    the buffer without first having said how many bytes it needed and how many
    were there. That is what makes every truncation arrive as an
    :class:`ObjectTruncatedError` rather than as a struct error or an index
    error carrying a fragment of the body.
    """

    def __init__(self, data: bytes) -> None:
        """Start at offset zero.

        Args:
            data: The body. Never copied wholesale, never echoed.
        """
        self._data = data
        self.offset = 0

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
            ObjectTruncatedError: Fewer than ``count`` bytes remain.
        """
        if count > self.remaining:
            raise ObjectTruncatedError(
                REASON_SHORT_BUFFER,
                field=field,
                offset=self.offset,
                expected=count,
                actual=self.remaining,
            )

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

    def floats(self, count: int, field: str) -> tuple[float, ...]:
        """Read ``count`` consecutive float32 values.

        Args:
            count: How many floats.
            field: The field being read.

        Returns:
            The values, in file order.
        """
        width = count * INT32_SIZE
        self._require(width, field)
        values = struct.unpack_from(f"<{count}f", self._data, self.offset)
        self.offset += width
        return tuple(float(value) for value in values)

    def string(self, field: str) -> str:
        """Read and decode one length-prefixed string.

        THE BOUND IS APPLIED TO THE BYTE COUNT, before the remaining length is
        consulted and before any slice is taken. The multiply on the UTF-16
        path happens first for exactly that reason: a declared character count
        just under the cap becomes a byte count just over it.

        Args:
            field: The field being read.

        Returns:
            The decoded text, without its trailing null.

        Raises:
            ObjectFormatError: The declared length is above
                :data:`MAX_STRING_BYTES`, or the bytes do not decode.
            ObjectTruncatedError: The declared payload runs past the body.
        """
        at = self.offset
        count = self.int32(field)
        if count == 0:
            return ""
        if count < 0:
            byte_count = -count * UTF16_CHAR_SIZE
            terminator = UTF16_CHAR_SIZE
            encoding = "utf-16-le"
        else:
            byte_count = count
            terminator = 1
            encoding = "utf-8"
        if byte_count > MAX_STRING_BYTES:
            raise ObjectFormatError(
                REASON_DECLARED_LENGTH_ABOVE_CAP,
                field=field,
                offset=at,
                expected=MAX_STRING_BYTES,
                actual=byte_count,
            )
        self._require(byte_count, field)
        raw = self._data[self.offset : self.offset + byte_count - terminator]
        self.offset += byte_count
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            # Re-raised from None: a UnicodeDecodeError message QUOTES the
            # offending bytes, and exception context is an echo path.
            raise ObjectFormatError(
                REASON_UNDECODABLE_TEXT, field=field, offset=at, actual=byte_count
            ) from None


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def transform_delta(save_version: int) -> int:
    """Look up the MEASURED transform delta for a save version.

    Args:
        save_version: The save version, from the header.

    Returns:
        The filler width in bytes.

    Raises:
        UnsupportedSaveVersionError: No delta has been measured for it. Never
            interpolated from its neighbours - see the module docstring.
    """
    delta = TRANSFORM_DELTA_BY_SAVE_VERSION.get(save_version)
    if delta is None:
        raise UnsupportedSaveVersionError(
            REASON_UNMEASURED_TRANSFORM_DELTA,
            field="save_version",
            offset=0,
            version=save_version,
        )
    return delta


def body_prefix_width(header_version: int) -> int:
    """How many bytes the body length prefix occupies on this header version.

    Args:
        header_version: The header version, from the header.

    Returns:
        8 on header versions 13 and 14, 4 on header version 10.
    """
    if header_version >= HEADER_VERSION_WITH_WIDE_PREFIX:
        return BODY_PREFIX_WIDTH_WIDE
    return BODY_PREFIX_WIDTH_NARROW


def class_name_of(type_path: str) -> str:
    """Reduce a class path to the object name a usmap schema is keyed by.

    The shipped property mapping keys its schemas by object name, so this is
    the one rule that joins the two. A path with no dot is already a bare
    name and is returned unchanged, which is what keeps a mod-authored or
    hand-written identifier from silently resolving to an empty string.

    Args:
        type_path: The class path as read, namespaced or bare.

    Returns:
        The text after the final dot, or the whole input when there is none.
    """
    return type_path.rpartition(".")[2] if "." in type_path else type_path


# ---------------------------------------------------------------------------
# The walk
# ---------------------------------------------------------------------------


def _warning(
    code: str, offset: int, *, expected: int | None = None, actual: int | None = None
) -> ObjectWarning:
    """Build one warning from the fixed detail table.

    Args:
        code: One of the ``WARN_*`` constants.
        offset: Where the condition was noticed.
        expected: An expected length or count.
        actual: An observed length or count.

    Returns:
        The warning.
    """
    return ObjectWarning(
        code=code, detail=_WARNING_DETAIL[code], offset=offset, expected=expected, actual=actual
    )


def _read_record(cursor: _Cursor, delta: int) -> ObjectRecord:
    """Read one object record at the cursor.

    Args:
        cursor: Positioned at the record's object-type discriminator.
        delta: The save version's filler width before the transform block.

    Returns:
        The record.

    Raises:
        ObjectFormatError: The discriminator has no measured record grammar.
        ObjectTruncatedError: The record runs past the body.
    """
    at = cursor.offset
    object_type = cursor.int32("object_type")
    kind = _KIND_BY_OBJECT_TYPE.get(object_type)
    if kind is None:
        raise ObjectFormatError(
            REASON_UNMEASURED_OBJECT_TYPE, field="object_type", offset=at, actual=object_type
        )

    type_path = cursor.string("type_path")
    root_object = cursor.string("root_object")
    instance_name = cursor.string("instance_name")

    # Opaque by measurement: only the WIDTH of this run is known (ADR 0003).
    # Decoding fields out of it would be decoding an invention.
    cursor.skip(delta, "transform_delta")

    values = cursor.floats(TRANSFORM_FLOAT_COUNT, "transform")
    was_placed_in_level = cursor.int32("was_placed_in_level")

    return ObjectRecord(
        kind=kind,
        type_path=type_path,
        root_object=root_object,
        instance_name=instance_name,
        transform=Transform(
            rotation=(values[0], values[1], values[2], values[3]),
            translation=(values[4], values[5], values[6]),
            scale=(values[7], values[8], values[9]),
        ),
        parent=None,
        object_type=object_type,
        was_placed_in_level=was_placed_in_level,
        body_offset=0,
        body_length=0,
    )


def _read_prefix(cursor: _Cursor, header_version: int) -> tuple[int, int, list[ObjectWarning]]:
    """Read the body length prefix at the version-appropriate width.

    Args:
        cursor: Positioned at byte zero of the body.
        header_version: Drives the width, and only the width.

    Returns:
        The declared length, the width used, and any advisories.
    """
    found: list[ObjectWarning] = []
    if header_version not in MEASURED_HEADER_VERSIONS:
        found.append(_warning(WARN_UNMEASURED_HEADER_VERSION, 0, actual=header_version))

    width = body_prefix_width(header_version)
    declared = (
        cursor.int64("body_length")
        if width == BODY_PREFIX_WIDTH_WIDE
        else cursor.int32("body_length")
    )
    if declared != cursor.remaining:
        found.append(
            _warning(
                WARN_BODY_LENGTH_DISAGREEMENT,
                0,
                expected=declared,
                actual=cursor.remaining,
            )
        )
    return declared, width, found


def _read_count(cursor: _Cursor, delta: int) -> int:
    """Read and bound the declared record count.

    The ceiling is checked BEFORE the buffer bound, so a wildly declared count
    is refused as a budget failure rather than reported as a truncation - the
    two mean different things to a caller and the ordering is what keeps them
    distinguishable.

    Args:
        cursor: Positioned at the count.
        delta: The save version's filler width, part of the minimum record size.

    Returns:
        The count.

    Raises:
        ObjectFormatError: The count is negative.
        ObjectBudgetExceededError: The count exceeds :data:`MAX_OBJECTS`.
        ObjectTruncatedError: The declared records cannot fit in the body.
    """
    at = cursor.offset
    count = cursor.int32("object_count")
    if count < 0:
        raise ObjectFormatError(
            REASON_NEGATIVE_COUNT, field="object_count", offset=at, actual=count
        )
    if count > MAX_OBJECTS:
        raise ObjectBudgetExceededError(
            REASON_ABOVE_CEILING,
            field="object_count",
            offset=at,
            expected=MAX_OBJECTS,
            actual=count,
        )
    needed = count * (_MINIMUM_RECORD_BYTES + delta)
    if needed > cursor.remaining:
        raise ObjectTruncatedError(
            REASON_SHORT_BUFFER,
            field="object_table",
            offset=cursor.offset,
            expected=needed,
            actual=cursor.remaining,
        )
    return count


class _UnknownLog:
    """Aggregates unmodelled class paths, keeping first-seen order.

    Order is stable so two runs on one save agree exactly, which the
    determinism property in CLAUDE.md section 1 requires of everything that
    reaches a rendering.
    """

    def __init__(self) -> None:
        """Start an empty log."""
        self._order: list[str] = []
        self._count: dict[str, int] = {}
        self._first: dict[str, int] = {}

    def add(self, type_path: str, index: int) -> None:
        """Record one unmodelled record.

        Args:
            type_path: The class path.
            index: The record index it was seen at.
        """
        if type_path not in self._count:
            self._order.append(type_path)
            self._count[type_path] = 0
            self._first[type_path] = index
        self._count[type_path] += 1

    def emit(self) -> tuple[UnknownClass, ...]:
        """Publish in first-seen order.

        Returns:
            The aggregated entries.
        """
        return tuple(
            UnknownClass(
                type_path=path,
                count=self._count[path],
                reason=REASON_CLASS_NOT_MODELLED,
                first_index=self._first[path],
            )
            for path in self._order
        )


def parse_object_headers(
    body: bytes,
    *,
    save_version: int,
    header_version: int,
    known_classes: Container[str] | None = None,
) -> ObjectTable:
    """Walk the object record table out of a decompressed save body.

    THE TWO DISPATCHES ARE INDEPENDENT. ``header_version`` selects the body
    length prefix width and NOTHING else; ``save_version`` selects the
    transform delta and NOTHING else. See the module docstring for why a parser
    conflating them passes every real-shaped fixture.

    THE WALK CONTINUES PAST UNKNOWN CONTENT. A class path the registry does not
    model is recorded and stepped over; parsing runs to the end of the table
    and the result reports that the world holds unmodelled content.

    Args:
        body: The decompressed body exactly as ``chunks.decompress_body``
            returns it, length prefix included.
        save_version: From the header. Drives the transform delta.
        header_version: From the header. Drives the length prefix width.
        known_classes: Class NAMES the caller can model - a property map's
            ``schemas`` mapping satisfies this directly. None means no registry
            was supplied and nothing is claimed unknown.

    Returns:
        The walked table, with everything flagged and carried.

    Raises:
        UnsupportedSaveVersionError: The save version has no measured transform
            delta. Raised before any byte of the table is read.
        ObjectTruncatedError: The body ends inside the table.
        ObjectFormatError: A count, a declared string length or an object-type
            discriminator is structurally impossible.
        ObjectBudgetExceededError: The declared record count exceeds the stated
            ceiling.
    """
    # EAGER, before a single byte of the table. A version check placed after
    # the walk cannot fire on an empty table and becomes a time bomb.
    delta = transform_delta(save_version)

    cursor = _Cursor(body)
    declared, width, warnings = _read_prefix(cursor, header_version)

    table_start = cursor.offset
    count = _read_count(cursor, delta)

    records: list[ObjectRecord] = []
    unknown = _UnknownLog()
    for index in range(count):
        record = _read_record(cursor, delta)
        records.append(record)
        if known_classes is not None and class_name_of(record.type_path) not in known_classes:
            unknown.add(record.type_path, index)

    consumed = cursor.offset - table_start
    if cursor.remaining:
        warnings.append(
            _warning(WARN_UNPARSED_DATA_SECTION, cursor.offset, actual=cursor.remaining)
        )

    return ObjectTable(
        records=tuple(records),
        unknown_classes=unknown.emit(),
        warnings=tuple(warnings),
        declared_body_length=declared,
        body_consumed=consumed,
        body_prefix_width=width,
        transform_delta=delta,
        save_version=save_version,
        header_version=header_version,
    )


# ---------------------------------------------------------------------------
# Property resolution
# ---------------------------------------------------------------------------


def read_properties(body: bytes, record: ObjectRecord, property_map: PropertyMap) -> PropertyResult:
    """Resolve one record against the property mapping and report what is missing.

    WHAT THIS DOES AND DOES NOT DO. It resolves the record's class path to a
    usmap schema and reports whether the mapping models that class. It decodes
    NO property value, because the object data section's grammar has never been
    measured by this project and no fixture carries one. A payload with a
    non-zero extent is FLAGGED as unparsed rather than guessed at.

    Nothing here raises for unknown content. A class the mapping cannot resolve
    is a reported state, not a failure (non-negotiable 7).

    Args:
        body: The decompressed body the record was walked out of.
        record: The record to resolve.
        property_map: The parsed mapping. Non-optional: handling the
            no-install None is the world layer's job, not this one's.

    Returns:
        What resolved, what did not, and why.

    Raises:
        ObjectTruncatedError: The record's declared payload extent runs past
            the body. A structural impossibility rather than unknown content.
    """
    name = class_name_of(record.type_path)
    if name not in property_map.schemas:
        return PropertyResult(
            properties=MappingProxyType({}),
            schema_name=name,
            resolved=False,
            warnings=(_warning(WARN_UNRESOLVED_SCHEMA, record.body_offset),),
        )

    if record.body_length == 0:
        # The NORMAL case for a large share of a real world. ADR 0003: a save
        # stores deltas from level defaults, so an actor whose properties are
        # all defaults carries no payload at all. Not unknown content.
        return PropertyResult(
            properties=MappingProxyType({}), schema_name=name, resolved=True, warnings=()
        )

    end = record.body_offset + record.body_length
    if record.body_offset < 0 or end > len(body):
        raise ObjectTruncatedError(
            REASON_SHORT_BUFFER,
            field="property_payload",
            offset=record.body_offset,
            expected=record.body_length,
            actual=max(len(body) - record.body_offset, 0),
        )

    return PropertyResult(
        properties=MappingProxyType({}),
        schema_name=name,
        resolved=True,
        warnings=(
            _warning(WARN_UNPARSED_PROPERTY_PAYLOAD, record.body_offset, actual=record.body_length),
        ),
    )


def parse_properties(
    body: bytes, record: ObjectRecord, property_map: PropertyMap
) -> Mapping[str, object]:
    """Resolve one record's properties, discarding the diagnostics.

    The thin accessor over :func:`read_properties` for a caller that wants only
    the mapping. Prefer the detailed form anywhere the flagged state matters -
    an empty mapping alone cannot tell "this class has no properties" from
    "this class is not modelled".

    Args:
        body: The decompressed body the record was walked out of.
        record: The record to resolve.
        property_map: The parsed mapping.

    Returns:
        The decoded properties. Always empty today - see
        :func:`read_properties`.
    """
    return read_properties(body, record, property_map).properties
