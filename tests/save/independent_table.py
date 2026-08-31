"""A SECOND EXPRESSION OF THE RECORD TABLE - CS-829's denominator arm.

WHY A SECOND ONE EXISTS AT ALL. ``tests/save/test_struct_interior.py`` grades a
struct-site population that is independent of the TAG READER and is NOT
independent of the RECORD TABLE. Both readings in that sweep iterate one
``objects.parse_body(...).records`` and consume the same three fields - kind,
payload offset, payload length - so a defect in the record table moves the
shipped count and the independent count together and reddens nothing. The
counter-example the session-40 adversary recorded is exactly that shape: relabel
every actor non-actor for one version pair and shift each non-actor payload
start by a byte, and both readings take the same wrong start, refuse together,
and every arm stays green while eighteen per cent of the sites vanish.

This module reads the same grammar and SHARES NO FUNCTION WITH IT. It calls
``struct.unpack_from`` and slices bytes; the only things it takes from
``clockspeed.save.objects`` are CONSTANTS - widths, ceilings, terminator names
and the per-pair layout table - which are DATA rather than readers. That is the
same line ``_independent_tag_walk`` already draws in the test module's "A SECOND
EXPRESSION OF THE TAG-LIST GRAMMAR" block, and
``tests/save/test_independent_table.py`` forces it statically: no attribute of
the shipped module may be called, and every attribute this module names must
resolve to a non-callable object.

THE KIND DISCRIMINATOR IS RE-TRANSCRIBED RATHER THAN IMPORTED, and it is the one
place where "constants yes" was not good enough. ``objects._KIND_BY_OBJECT_TYPE``
is the exact table the recorded counter-example relabels, so importing it would
put the kind decision back on the shipped side of the seam. The two spellings are
cross-checked by
``tests/save/test_independent_table.py::test_the_object_type_transcription_matches_the_shipped_discriminator_table``
so they cannot drift apart in silence.

WHAT THIS SEPARATION DOES NOT COVER, NAMED RATHER THAN IMPLIED AWAY. Both
readings consult ONE ``objects.BODY_LAYOUT_BY_PAIR``, so a defect planted in the
layout table itself - a wrong ``transform_delta``, a flipped
``component_pre_word`` - moves both and this module reddens nothing. That is a
deliberate limit of the seam and not an oversight: the layout is DATA both
readings have to agree on to be reading the same format at all. The compensating
control is elsewhere and it is a second transcription rather than a second
reader - ``tests/save/synthetic.py`` writes bodies from its own copy of the
table and
``tests/save/test_objects.py::test_the_layout_table_is_transcribed_from_the_corpus_field_by_field``
compares the two field by field.

IT IS DELIBERATELY CONSERVATIVE AND ONE-SIDED. Declining a record is always
allowed; inventing one is not. Two declines are built in and they are different
sizes:

- A LEVEL whose record count and payload-extent count disagree contributes NO
  record. ``objects._attribute_payloads`` leaves such records with a zero extent
  and flags the level; a zero extent is an INVENTED extent for this module's
  purpose, so the level is dropped and the walk continues. No real save on this
  machine has ever reached that branch.
- THE WHOLE SAVE is declined the moment any read stops being certain - a short
  buffer, a count above its ceiling, a section whose walked extent disagrees with
  its declared size, an object-type discriminator outside the measured two.
  Resuming after a desynchronised cursor is the one thing that could manufacture
  a record, and returning the records read so far would hand back a silently
  truncated table wearing the shape of a complete one. That is the same trap as
  an empty population satisfying every zero, so it is refused outright.

NO STRING LEAVES THIS MODULE AND NONE IS EVER BOUND. Every string in the
grammar - a level name, a class path, a root object, an instance name, a
component's parent path, a collectable, a package name, a grid cell - is world
content that non-negotiable 12 keeps out of every echo path. They are STEPPED
OVER by length. The one place bytes are decoded at all is the decodability check
in :meth:`_Reader.string`, whose result is discarded in the same expression and
never bound, because a body the shipped walk refuses as undecodable must be
refused here too or this reading would accept something the shipped walk does
not.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Final

from clockspeed.save import objects

#: The object-type discriminator, RE-TRANSCRIBED. See the module docstring for
#: why this is not imported from the shipped table it is checked against.
_OBJECT_TYPE_ACTOR: Final = 1
_OBJECT_TYPE_COMPONENT: Final = 0


@dataclass(frozen=True)
class IndependentRecord:
    """One record located WITHOUT the shipped record table. COUNTS AND OFFSETS ONLY.

    Attributes:
        is_actor: Whether the record's discriminator is the measured actor word.
        body_offset: The first byte of this record's payload, in the body.
        body_length: How many bytes that payload declares.
    """

    is_actor: bool
    body_offset: int
    body_length: int


class _DeclineError(Exception):
    """Raised the instant this reading stops being certain. CARRIES NOTHING.

    It takes no argument at any raise site and none is added later. An exception
    raised out of a walk over a personal-data-bearing body is an echo path, and
    the cheapest way to guarantee it carries nothing is to give it nothing to
    carry.
    """


class _Reader:
    """A bounds-checked forward reader over one body, owned by this module.

    Every read goes through :meth:`_need`, so there is no path that indexes the
    buffer without first having said how many bytes it needed and how many were
    there.
    """

    __slots__ = ("_body", "offset")

    def __init__(self, body: bytes) -> None:
        """Start at byte zero.

        Args:
            body: The decompressed body. Never copied wholesale, never echoed.
        """
        self._body = body
        self.offset = 0

    def _need(self, count: int) -> None:
        """Assert ``count`` bytes are available at the cursor.

        Args:
            count: Bytes needed. A negative count is a desynchronised walk
                rather than a request, and is refused on the same terms.

        Raises:
            _DeclineError: The request is impossible.
        """
        if count < 0 or count > len(self._body) - self.offset:
            raise _DeclineError

    def int32(self) -> int:
        """Read one signed 32-bit little-endian integer.

        Returns:
            The value.
        """
        self._need(objects.INT32_SIZE)
        (value,) = struct.unpack_from("<i", self._body, self.offset)
        self.offset += objects.INT32_SIZE
        return int(value)

    def skip(self, count: int) -> None:
        """Step over a run of bytes without reading them.

        Args:
            count: How many bytes to step over.
        """
        self._need(count)
        self.offset += count

    def bounded(self, ceiling: int) -> int:
        """Read a count and refuse an impossible one before anything is allocated.

        Args:
            ceiling: The stated maximum.

        Returns:
            The count.

        Raises:
            _DeclineError: The count is negative or above the ceiling.
        """
        value = self.int32()
        if value < 0 or value > ceiling:
            raise _DeclineError
        return value

    def string(self) -> None:
        """Step over one length-prefixed string WITHOUT returning it.

        A negative count selects UTF-16-LE and its magnitude is a CHARACTER
        count, so the byte count is twice it. The bound is applied to the BYTE
        count, before the remaining length is consulted and before any slice is
        taken - a declared character count just under the cap becomes a byte
        count just over it.

        THE DECODE IS A CHECK AND NOT A READ. Its result is discarded in the
        same expression and never bound. It happens at all because the shipped
        walk refuses a body carrying undecodable text, and a reading that sailed
        past one would accept a record the shipped walk refuses - which is the
        one direction this module is not allowed to be wrong in.

        Raises:
            _DeclineError: The declared length is above the cap, runs past the
                body, or the bytes do not decode.
        """
        declared = self.int32()
        if declared == 0:
            return
        if declared > 0:
            width, terminator, encoding = declared, 1, "utf-8"
        else:
            width = -declared * objects.UTF16_CHAR_SIZE
            terminator, encoding = objects.UTF16_CHAR_SIZE, "utf-16-le"
        if width > objects.MAX_STRING_BYTES:
            raise _DeclineError
        self._need(width)
        try:
            self._body[self.offset : self.offset + width - terminator].decode(encoding)
        except UnicodeDecodeError:
            # Raised `from None`: a UnicodeDecodeError message QUOTES the
            # offending bytes and exception context is an echo path.
            raise _DeclineError from None
        self.offset += width


def _step_collectables(reader: _Reader) -> None:
    """Step over one collectable list - a count then that many PAIRS of strings.

    Args:
        reader: Positioned at the count.
    """
    for _ in range(reader.bounded(objects.MAX_OBJECTS)):
        reader.string()
        reader.string()


def _step_package_summary(reader: _Reader) -> None:
    """Step over one package summary.

    Two strings around an opaque middle run, a count, then that many fixed-width
    entries.

    Args:
        reader: Positioned at the summary.
    """
    reader.string()
    reader.skip(objects._PACKAGE_SUMMARY_MIDDLE_BYTES)  # noqa: SLF001 - a width, not a reader
    reader.string()
    count = reader.bounded(objects.MAX_CUSTOM_VERSIONS)
    reader.skip(count * objects._CUSTOM_VERSION_ENTRY_BYTES)  # noqa: SLF001 - a width


def _step_grid_preamble(reader: _Reader) -> None:
    """Step over the grid block that precedes the level count on three pairs.

    Args:
        reader: Positioned at the grid count.
    """
    for _ in range(reader.bounded(objects.MAX_GRIDS)):
        reader.string()
        reader.skip(objects._GRID_OPAQUE_BYTES)  # noqa: SLF001 - a width, not a reader
        for _ in range(reader.bounded(objects.MAX_OBJECTS)):
            reader.string()
            reader.skip(objects._GRID_CELL_OPAQUE_BYTES)  # noqa: SLF001 - a width


def _step_level_tail(reader: _Reader) -> None:
    """Step over a named level's tail: two opaque words bracketing a string-pair list.

    Args:
        reader: Positioned at the tail.
    """
    reader.skip(objects._LEVEL_TAIL_LEAD_BYTES)  # noqa: SLF001 - a width, not a reader
    for _ in range(reader.bounded(objects.MAX_LEVEL_TAIL_ENTRIES)):
        reader.string()
        reader.string()
    reader.skip(objects._LEVEL_TAIL_TRAILING_BYTES)  # noqa: SLF001 - a width


def _section_size(reader: _Reader, layout: objects.BodyLayout) -> int:
    """Read one section size at the pair's width.

    An 8-byte size is an int32 size followed by a reserved int32. The reserved
    word is CONSUMED AND NOT INTERPRETED here: the shipped walk flags a non-zero
    one rather than refusing, so refusing on it would make this reading decline
    a body the shipped walk accepts - allowed, but for no gain.

    Args:
        reader: Positioned at the size.
        layout: The pair's grammar, for the width.

    Returns:
        The declared size.
    """
    size = reader.int32()
    if layout.section_size_width != objects.INT32_SIZE:
        reader.int32()
    return size


def _step_record(reader: _Reader, layout: objects.BodyLayout) -> bool:
    """Step over one record's header and report only its KIND.

    THE TWO KINDS DIVERGE HERE and they consume different bytes: an actor closes
    with its opaque run, its transform block and a trailing int32; a component
    closes with a parent path, preceded on two pairs by an opaque word. Reading
    the actor shape under either discriminator desynchronises a real body at its
    first component.

    Every string is stepped over. Nothing this function reads is returned except
    one boolean.

    Args:
        reader: Positioned at the record's object-type discriminator.
        layout: The pair's grammar.

    Returns:
        Whether the record carries the measured actor discriminator.

    Raises:
        _DeclineError: The discriminator is outside the measured two, which is
            an unknown GRAMMAR rather than an unknown class - it decides how
            many bytes the record occupies, so guessing it makes everything
            after it invention.
    """
    discriminator = reader.int32()
    if discriminator == _OBJECT_TYPE_ACTOR:
        is_actor = True
    elif discriminator == _OBJECT_TYPE_COMPONENT:
        is_actor = False
    else:
        raise _DeclineError

    # The type path, the root object and the instance name. All three are world
    # content and all three are stepped over (non-negotiable 12).
    reader.string()
    reader.string()
    reader.string()

    if is_actor:
        reader.skip(layout.transform_delta)
        reader.skip(objects.TRANSFORM_BYTES)
        reader.int32()
    else:
        if layout.component_pre_word:
            reader.skip(objects._COMPONENT_PRE_WORD_BYTES)  # noqa: SLF001 - a width
        reader.string()
    return is_actor


def _step_data_entries(reader: _Reader, layout: objects.BodyLayout) -> list[tuple[int, int]]:
    """Walk one level's object data section and LOCATE every payload in it.

    The payload's value grammar is not decoded; only its framing is, and the
    framing is what locates it.

    Args:
        reader: Positioned at the section's entry count.
        layout: The pair's grammar.

    Returns:
        One ``(offset, length)`` per entry, in file order.
    """
    extents: list[tuple[int, int]] = []
    for _ in range(reader.bounded(objects.MAX_OBJECTS)):
        if layout.data_entry_lead:
            reader.skip(layout.data_entry_lead)
        length = reader.bounded(objects.MAX_OBJECT_DATA_BYTES)
        extents.append((reader.offset, length))
        reader.skip(length)
        if layout.data_entry_trailer:
            reader.int32()
    return extents


def _walk_level(
    reader: _Reader, layout: objects.BodyLayout, *, named: bool, into: list[IndependentRecord]
) -> None:
    """Read one level: its record table, its data section, and the k-th attribution.

    ``named`` is False for exactly one level per body - the trailing persistent
    level. That asymmetry is measured; a walk expecting a name there stops with
    hundreds of thousands of bytes unread.

    THE HEADER BLOCK IS OPTIONAL AND THE RULE IS SIZE-DRIVEN: if bytes remain
    inside the declared header section once the record count is exhausted, those
    bytes are a collectable block. Both declared sizes are then checked against
    what was walked, which is this reading's own oracle and is applied at every
    level rather than once at the end.

    THE k-TH PAYLOAD BELONGS TO THE k-TH RECORD, and pairing is only DEFINED
    when the two counts agree. Where they do not, this level contributes NOTHING
    - see the module docstring.

    Args:
        reader: Positioned at the level.
        layout: The pair's grammar.
        named: Whether the level carries a leading name string.
        into: Accumulator, appended to in file order.

    Raises:
        _DeclineError: A declared section size disagrees with what was walked,
            or any read inside the level stops being certain.
    """
    if named:
        # The level name. Read by LENGTH and never held - it is world content.
        reader.string()

    header_size = _section_size(reader, layout)
    base = reader.offset
    count = reader.bounded(objects.MAX_OBJECTS)
    kinds = [_step_record(reader, layout) for _ in range(count)]
    if reader.offset - base < header_size:
        _step_collectables(reader)
    if reader.offset - base != header_size:
        raise _DeclineError

    data_size = _section_size(reader, layout)
    data_base = reader.offset
    extents = _step_data_entries(reader, layout)
    if reader.offset - data_base != data_size:
        raise _DeclineError

    if len(extents) == count:
        into.extend(
            IndependentRecord(is_actor=kind, body_offset=at, body_length=length)
            for kind, (at, length) in zip(kinds, extents, strict=True)
        )

    if named:
        if layout.level_tail == objects.LEVEL_TAIL_WORD:
            reader.int32()
        elif layout.level_tail == objects.LEVEL_TAIL_SUMMARY:
            _step_level_tail(reader)
            _step_package_summary(reader)
    if not named or layout.second_collectables_named:
        _step_collectables(reader)


def _walk_body(
    body: bytes, layout: objects.BodyLayout, header_version: int
) -> tuple[IndependentRecord, ...]:
    """Walk a whole body: prefix, optional preamble, every level, trailing word.

    Args:
        body: The decompressed body, length prefix included.
        layout: The pair's grammar.
        header_version: Drives the length prefix width, and only that.

    Returns:
        Every record every level could pair, in file order.

    Raises:
        _DeclineError: Any read stopped being certain.
    """
    reader = _Reader(body)
    # The body length prefix. Its WIDTH follows the header version; its VALUE is
    # stepped over rather than trusted, exactly as the shipped walk treats a
    # disagreement between it and the remaining length as advisory.
    reader.skip(
        objects.BODY_PREFIX_WIDTH_WIDE
        if header_version >= objects.HEADER_VERSION_WITH_WIDE_PREFIX
        else objects.BODY_PREFIX_WIDTH_NARROW
    )

    if layout.package_summary:
        _step_package_summary(reader)
    if layout.grid_preamble:
        _step_grid_preamble(reader)

    found: list[IndependentRecord] = []
    for _ in range(reader.bounded(objects.MAX_LEVELS)):
        _walk_level(reader, layout, named=True, into=found)
    # Exactly one unnamed persistent level closes every measured body.
    _walk_level(reader, layout, named=False, into=found)
    # Measured as present and observed to be zero. Its MEANING is unmeasured, so
    # it is consumed and not interpreted; a walk without it stops four bytes
    # short of the end of a real body.
    reader.int32()
    return tuple(found)


def independent_records(
    body: bytes, *, save_version: int, header_version: int
) -> tuple[IndependentRecord, ...] | None:
    """Locate every record's payload extent and kind by a second reading.

    Returns None when the pair has no measured layout - that is the version pair
    this project does not parse, and it is a DECLINE, never an empty tuple.
    An empty tuple means 'read the body and found no records', which is a
    different claim. See memory/an-empty-population-satisfies-every-zero.md.

    None ALSO carries the second decline - a body whose walk stopped being
    certain - and both meanings are the same answer to a caller: this reading
    has nothing to say. What None never means is zero. The module docstring
    states why a partial table is not returned instead.

    Args:
        body: The decompressed body exactly as ``chunks.decompress_body``
            returns it, length prefix included.
        save_version: From the header. Half of the layout key.
        header_version: From the header. The other half, and the prefix width.

    Returns:
        One record per payload this reading could pair, in file order, or None.
    """
    layout = objects.BODY_LAYOUT_BY_PAIR.get((header_version, save_version))
    if layout is None:
        return None
    try:
        return _walk_body(body, layout, header_version)
    except _DeclineError:
        return None
