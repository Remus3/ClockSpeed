"""Property-mapping loader: container framing, inner grammar, cache and limits.

WHAT IS MEASURED HERE AND WHAT IS BUILT
-----------------------------------------
The shipped ``FactoryGame.usmap`` inner grammar was DERIVED FROM THE BYTES and
is held in place by TWO controls of different strength. Which one covers which
fact matters, and ``synthetic.USMAP_EVIDENCE`` records that per field as data
rather than leaving it to prose.

THE LANDING CONTROL, ``test_the_real_usmap_accounts_for_its_own_length_exactly``
- the walk consumes the real name, enum and schema sections and lands EXACTLY
on a four-character printable-ASCII tag, with no unresolved name index, no
out-of-range type byte and no desynchronised section. It is decisive for most
fields and it is NOT sufficient, which was measured rather than assumed: it
asserted almost none of that until 2026-08-15, and even now it cannot see a
field ORDER swap that consumes the same bytes.

THE REBUILD CONTROL, ``test_the_builder_reproduces_the_shipped_bytes_it_models``
- every real enum and schema is re-emitted through the corpus builder and
compared to the GAME'S OWN BYTES. This is the only control here that cannot be
satisfied by a self-consistent wrong answer, and it is the one that closes the
common-mode risk CS-404 exists for. It caught a type-26 field-order error that
lands on the identical byte and passed the entire suite.

Both SKIP WITH A REASON where there is no install, so CI - which has none -
runs on neither. That is stated plainly rather than hidden: on a machine with
no game, this module grades the builder against itself.

``tests/save/synthetic.py`` is used for everything its builder actually models.
Its OUTER framing is measured and is reused verbatim here through
:func:`_reframe`, which copies the builder's own magic, version and compression
bytes and only corrects the two size fields.

Its DEFAULT inner grammar for ENUMS and SCHEMAS is a self-consistent
placeholder - its own docstring says so - and it does NOT match the shipped
file: it writes inline length-prefixed strings where the shipped format writes
uint32 indices into the name table, and it emits no property-type byte at all.
The NAMES section does match.

CHANGED 2026-08-15 (CS-404). ``build_usmap`` now also has a SHIPPED-GRAMMAR
MODE, ``shipped=True``, which writes the measured grammar, plus a ``version``
parameter that reaches the version-1 versioning block. Before that, the gap was
covered by :func:`_shipped_body` in this file - a second encoder, living beside
the tests it fed, which is a corpus that can only ever agree with whoever wrote
it. The corpus module owns the measurement now.

:func:`_shipped_body` is KEPT, for one reason and not the other. Not because
the grammar needs a second implementation - agreement between two encoders is
weak evidence, since both can be wrong the same way. It is kept because a
DISAGREEMENT would be decisive, and
``test_the_builders_shipped_mode_agrees_with_the_hand_built_body_byte_for_byte``
is what watches for one. Note its limit: it models the type-9 payload only, so
new tests should reach for ``build_usmap(shipped=True)``, which refuses a
descriptor it cannot write correctly instead of emitting a desynchronised body.

The synthetic round trip in section 8 asserts ``body_consumed ==
compressed_size``, which catches a grammar that is wrong about a WIDTH. It
cannot catch one that is wrong about an ORDER, because a swap consumes the same
bytes - that is what the rebuild control is for. Nineteen single-field
mutations of the builder have been run against this module across two rounds;
the one survivor is the custom-version filler BYTE, which is genuinely free.

NO REAL GAME DATA IS COMMITTED IN THIS FILE. Every name written below is
invented. The three tests that open the shipped file skip with a reason where
there is none, and report COUNTS, OFFSETS AND WIDTHS ONLY. Real names do flow
through the rebuild audit at runtime, so that audit CONTAINS ITS OWN
EXCEPTIONS and yields integers and an exception TYPE - pytest renders the
arguments of every frame in a failing traceback, measured, so an escaping
exception is an echo path (non-negotiable 12).
"""

from __future__ import annotations

import struct
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import pytest

from clockspeed.data.locate import (
    ENV_ACCOUNT_DIR,
    ENV_GAME_DIR,
    ENV_LOCAL_CONFIG,
    ENV_SAVE_ROOT,
    resolve_game_dir,
)
from clockspeed.save import usmap
from tests.save import synthetic

# --- fixture shapes, named so a comparison is never a magic literal ---------

_TWO_NAMES = 2
_ONE = 1
_TWO = 2
_THREE = 3
_ZERO = 0

#: A property type byte no shipped build uses, for the flag-and-skip test.
_UNKNOWN_TYPE = 0xEE

#: Shipped type ids this module's tests rely on, derived from the real file.
_TYPE_BOOL = 1
_TYPE_INT = 2
_TYPE_ARRAY = 8
_TYPE_STRUCT = 9
_TYPE_MAP = 24
_TYPE_SET = 25
_TYPE_ENUM_PROPERTY = 26

#: Container shapes the versioning-block tests assert against. Measured from
#: the shipped file - see the CS-404 note in tests/save/synthetic.py.
_VERSION_ZERO = 0
_VERSION_ONE = 1
_VERSION_UNKNOWN = 2
_CUSTOM_VERSION_RECORD_BYTES = 20
_CUSTOM_VERSION_CEILING = 4096

#: Header widths, derived by walking the fields rather than assumed.
_HEADER_NO_VERSIONING = 12
_HEADER_VERSIONING_OFF = 16
_HEADER_VERSIONING_ON = 32

#: The "no super type" sentinel, spelled again HERE on purpose. Comparing only
#: against ``synthetic.USMAP_NO_SUPER`` would make the assertion a restatement
#: of the builder's own opinion - the same control the independent reader in
#: tests/save/test_synthetic.py uses. A mutation narrowing the builder's
#: constant to 16 bits survived the version of this test that lacked it.
_ALL_BITS_SET = 0xFFFFFFFF

#: The trailing extension container opens with a four-byte tag. Asserted as a
#: WIDTH and a printable-ASCII range, never compared against the tag's letters -
#: the tag is shipped content.
_TAG_WIDTH = 4
_ASCII_SPACE = 0x20
_ASCII_DELETE = 0x7F

#: The real file nests descriptors at most 2 deep; the cap turns a corrupt run
#: into a caught RecursionError rather than a crash inside the audit.
_MAX_AUDIT_DEPTH = 16


# ---------------------------------------------------------------------------
# Builders for the grammar tests/save/synthetic.py does not model
# ---------------------------------------------------------------------------


def _reframe(framing_source: bytes, payload: bytes) -> bytes:
    """Wrap ``payload`` in the builder's own measured outer framing.

    Copies bytes 0..3 - magic, version and compression method - verbatim from
    a real ``synthetic.build_usmap`` result, so the framing under test is the
    corpus module's, not a second opinion about it. Only the two size fields
    are rewritten, because the payload differs.

    Args:
        framing_source: Any ``build_usmap`` output to take the framing from.
        payload: The body to frame.

    Returns:
        The framed usmap bytes.
    """
    size = struct.pack("<I", len(payload))
    return framing_source[:4] + size + size + payload


def _name_bytes(text: str) -> bytes:
    """Encode one name the way both the builder and the shipped file do."""
    raw = text.encode("utf-8")
    return struct.pack("<B", len(raw)) + raw


def _shipped_body(
    names: list[str],
    enums: list[tuple[str, list[str]]],
    schemas: list[tuple[str, str | None, list[tuple[str, int]]]],
) -> bytes:
    """Build the SHIPPED inner grammar, independently of ``build_usmap``.

    Derived from the shipped file and verified against it - see the module
    docstring. Enum and schema names are uint32 indices into the name table
    here, where ``build_usmap(shipped=False)`` writes inline strings.

    KEPT DELIBERATELY as the disagreement detector against
    ``build_usmap(shipped=True)``, which now models the same grammar. It writes
    the type-9 payload and no other, so it can silently emit a desynchronised
    body for an array, set, map or enum property. Prefer the builder.

    Args:
        names: The name table.
        enums: ``(enum name, member names)``. Every name must be in ``names``.
        schemas: ``(name, super name or None, [(property name, type id)])``.

    Returns:
        The body bytes, with no outer framing.
    """
    index = {text: position for position, text in enumerate(names)}
    out = [struct.pack("<I", len(names))]
    out.extend(_name_bytes(text) for text in names)

    out.append(struct.pack("<I", len(enums)))
    for enum_name, members in enums:
        out.append(struct.pack("<I", index[enum_name]))
        out.append(struct.pack("<B", len(members)))
        out.extend(struct.pack("<I", index[member]) for member in members)

    out.append(struct.pack("<I", len(schemas)))
    for schema_name, super_name, properties in schemas:
        out.append(struct.pack("<I", index[schema_name]))
        out.append(struct.pack("<I", 0xFFFFFFFF if super_name is None else index[super_name]))
        out.append(struct.pack("<H", len(properties)))
        out.append(struct.pack("<H", len(properties)))
        for slot, (property_name, type_id) in enumerate(properties):
            out.append(struct.pack("<H", slot))
            out.append(struct.pack("<B", 1))
            out.append(struct.pack("<I", index[property_name]))
            out.append(struct.pack("<B", type_id))
            if type_id == _TYPE_STRUCT:
                out.append(struct.pack("<I", index[property_name]))
    return b"".join(out)


def _no_install(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Point all four CLOCKSPEED_* overrides at paths that do not exist."""
    missing = tmp_path / "absent"
    for variable in (ENV_GAME_DIR, ENV_SAVE_ROOT, ENV_ACCOUNT_DIR):
        monkeypatch.setenv(variable, str(missing))
    monkeypatch.setenv(ENV_LOCAL_CONFIG, str(tmp_path / "absent.json"))
    usmap.clear_cache()


# ---------------------------------------------------------------------------
# 1 - an uncompressed usmap parses
# ---------------------------------------------------------------------------


def test_an_uncompressed_usmap_from_the_shared_builder_recovers_its_names() -> None:
    """The NAMES section is the part build_usmap and the shipped file agree on."""
    blob = synthetic.build_usmap(names=["Alpha", "Beta"], enums=[], schemas=[])

    parsed = usmap.parse_usmap(blob)

    assert parsed.names == ("Alpha", "Beta")
    assert len(parsed.names) == _TWO_NAMES
    assert parsed.enums == {}
    assert parsed.schemas == {}
    assert parsed.container.compression_method == usmap.COMPRESSION_NONE


def test_an_uncompressed_usmap_recovers_its_names_enums_and_schemas() -> None:
    """Names, enums AND schemas all come back from a compression-method-0 usmap."""
    names = ["Alpha", "Beta", "ESynthEnum", "Member0", "Member1", "SynthSchema", "SynthBase"]
    body = _shipped_body(
        names=names,
        enums=[("ESynthEnum", ["Member0", "Member1"])],
        schemas=[("SynthSchema", "SynthBase", [("Alpha", _TYPE_INT), ("Beta", _TYPE_BOOL)])],
    )
    blob = _reframe(synthetic.build_usmap(names=[], enums=[], schemas=[]), body)

    parsed = usmap.parse_usmap(blob)

    assert parsed.names == tuple(names)
    assert parsed.enums == {"ESynthEnum": ("Member0", "Member1")}
    assert set(parsed.schemas) == {"SynthSchema"}
    schema = parsed.schemas["SynthSchema"]
    assert schema.name == "SynthSchema"
    assert schema.super_name == "SynthBase"
    assert [entry.name for entry in schema.properties] == ["Alpha", "Beta"]
    assert [entry.type_id for entry in schema.properties] == [_TYPE_INT, _TYPE_BOOL]
    assert parsed.warnings == ()


def test_a_schema_with_no_super_reports_none_rather_than_a_sentinel() -> None:
    body = _shipped_body(
        names=["Alpha", "SynthSchema"],
        enums=[],
        schemas=[("SynthSchema", None, [("Alpha", _TYPE_INT)])],
    )
    blob = _reframe(synthetic.build_usmap(names=[], enums=[], schemas=[]), body)

    parsed = usmap.parse_usmap(blob)

    assert parsed.schemas["SynthSchema"].super_name is None


# ---------------------------------------------------------------------------
# 2 - an unsupported compression method is one clean error
# ---------------------------------------------------------------------------


def test_an_unsupported_compression_method_raises_naming_the_method_integer() -> None:
    """Method 1 is Oodle: it needs an external decompressor behind a license gate."""
    blob = synthetic.usmap_with_compression(synthetic.USMAP_COMPRESSION_OODLE)

    with pytest.raises(usmap.UnsupportedUsmapCompressionError) as caught:
        usmap.parse_usmap(blob)

    assert caught.value.method == synthetic.USMAP_COMPRESSION_OODLE
    assert str(synthetic.USMAP_COMPRESSION_OODLE) in str(caught.value)
    assert isinstance(caught.value, usmap.UsmapError)


@pytest.mark.parametrize(
    "method",
    [
        synthetic.USMAP_COMPRESSION_OODLE,
        synthetic.USMAP_COMPRESSION_BROTLI,
        synthetic.USMAP_COMPRESSION_ZSTD,
    ],
)
def test_every_compression_method_other_than_zero_is_refused(method: int) -> None:
    with pytest.raises(usmap.UnsupportedUsmapCompressionError) as caught:
        usmap.parse_usmap(synthetic.usmap_with_compression(method))

    assert caught.value.method == method


# ---------------------------------------------------------------------------
# 3 - no install is None, never an exception
# ---------------------------------------------------------------------------


def test_cached_usmap_returns_none_with_no_install_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """CI runs on a machine that has never had the game on it."""
    _no_install(monkeypatch, tmp_path)

    assert usmap.cached_usmap() is None


def test_default_usmap_path_returns_none_with_no_install_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _no_install(monkeypatch, tmp_path)

    assert usmap.default_usmap_path() is None


def test_cached_usmap_is_none_when_the_install_has_no_usmap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A directory that exists but holds no mapping file is absence, not failure."""
    monkeypatch.setenv(ENV_GAME_DIR, str(tmp_path))
    monkeypatch.setenv(ENV_LOCAL_CONFIG, str(tmp_path / "absent.json"))
    usmap.clear_cache()

    assert usmap.cached_usmap() is None


# ---------------------------------------------------------------------------
# 4 - truncation is a UsmapFormatError, never an IndexError or a struct.error
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("keep", [0, 1, 2, 3, 5, 8, 11, 12, 13, 16, 20])
def test_a_truncated_usmap_raises_a_format_error(keep: int) -> None:
    """Every truncation point, header and body alike, is one clean error."""
    blob = synthetic.build_usmap(
        names=["Alpha", "Beta"],
        enums=[],
        schemas=[],
    )

    with pytest.raises(usmap.UsmapFormatError) as caught:
        usmap.parse_usmap(blob[:keep])

    assert isinstance(caught.value, usmap.UsmapError)


def test_a_truncated_usmap_body_does_not_leak_a_struct_error() -> None:
    body = _shipped_body(
        names=["Alpha", "SynthSchema"],
        enums=[],
        schemas=[("SynthSchema", None, [("Alpha", _TYPE_INT)])],
    )
    blob = _reframe(synthetic.build_usmap(names=[], enums=[], schemas=[]), body)

    with pytest.raises(usmap.UsmapFormatError):
        usmap.parse_usmap(blob[: len(blob) - 3])


def test_a_wrong_magic_is_a_format_error() -> None:
    blob = bytearray(synthetic.build_usmap(names=["Alpha"], enums=[], schemas=[]))
    blob[0] ^= 0xFF

    with pytest.raises(usmap.UsmapFormatError):
        usmap.parse_usmap(bytes(blob))


def test_a_declared_size_that_disagrees_with_the_body_is_a_format_error() -> None:
    blob = bytearray(synthetic.build_usmap(names=["Alpha"], enums=[], schemas=[]))
    struct.pack_into("<I", blob, 4, len(blob))

    with pytest.raises(usmap.UsmapFormatError):
        usmap.parse_usmap(bytes(blob))


# ---------------------------------------------------------------------------
# 5 - unknown content is flagged and skipped, never fatal
# ---------------------------------------------------------------------------


def test_an_unknown_property_type_is_flagged_and_skipped_and_parsing_continues() -> None:
    """The surrounding entries must still be there. That is the whole rule."""
    names = ["Before", "Strange", "After", "SynthSchema", "Tail"]
    body = _shipped_body(
        names=names,
        enums=[],
        schemas=[
            (
                "SynthSchema",
                None,
                [
                    ("Before", _TYPE_INT),
                    ("Strange", _UNKNOWN_TYPE),
                    ("After", _TYPE_BOOL),
                ],
            ),
            ("Tail", None, [("Before", _TYPE_INT)]),
        ],
    )
    blob = _reframe(synthetic.build_usmap(names=[], enums=[], schemas=[]), body)

    parsed = usmap.parse_usmap(blob)

    codes = [warning.code for warning in parsed.warnings]
    assert usmap.WARN_UNKNOWN_PROPERTY_TYPE in codes
    flagged = next(
        warning for warning in parsed.warnings if warning.code == usmap.WARN_UNKNOWN_PROPERTY_TYPE
    )
    assert str(_UNKNOWN_TYPE) in flagged.subject

    # The entry itself is SKIPPED ...
    schema = parsed.schemas["SynthSchema"]
    assert [entry.name for entry in schema.properties] == ["Before", "After"]
    # ... and everything after it still parsed, including the next schema.
    assert set(parsed.schemas) == {"SynthSchema", "Tail"}
    assert len(parsed.schemas["Tail"].properties) == _ONE


def test_an_unknown_property_type_never_raises() -> None:
    body = _shipped_body(
        names=["Only", "SynthSchema"],
        enums=[],
        schemas=[("SynthSchema", None, [("Only", _UNKNOWN_TYPE)])],
    )
    blob = _reframe(synthetic.build_usmap(names=[], enums=[], schemas=[]), body)

    parsed = usmap.parse_usmap(blob)

    assert parsed.schemas["SynthSchema"].properties == ()
    assert parsed.warnings != ()


def test_a_trailing_section_is_flagged_and_skipped_rather_than_failing() -> None:
    """The shipped file carries an extension block after the schemas."""
    body = _shipped_body(names=["Alpha"], enums=[], schemas=[]) + b"CEXT" + b"\x00" * 16
    blob = _reframe(synthetic.build_usmap(names=[], enums=[], schemas=[]), body)

    parsed = usmap.parse_usmap(blob)

    assert parsed.names == ("Alpha",)
    assert usmap.WARN_TRAILING_SECTION in [warning.code for warning in parsed.warnings]


def test_a_schema_section_that_runs_short_is_flagged_rather_than_invented() -> None:
    """Never silently wrong: a section that cannot be trusted ends in a warning.

    This is the second half of the flag-and-skip rule. Skipping a property type
    whose payload width is unknown can leave the cursor mid-entry, and the only
    honest response to that is to say how much was lost - not to keep reading
    misaligned bytes and publish whatever they happen to spell.
    """
    body = _shipped_body(
        names=["Alpha", "First", "Second"],
        enums=[],
        schemas=[
            ("First", None, [("Alpha", _TYPE_INT)]),
            ("Second", None, [("Alpha", _TYPE_INT)]),
        ],
    )
    # Cut the second schema short, then reframe so the CONTAINER stays
    # self-consistent - the subject here is the schema section, not the
    # container's own length check.
    blob = _reframe(synthetic.build_usmap(names=[], enums=[], schemas=[]), body[: len(body) - 6])

    parsed = usmap.parse_usmap(blob)

    assert usmap.WARN_DESYNCHRONISED_SECTION in [warning.code for warning in parsed.warnings]
    # What WAS read is kept; what could not be is reported, not invented.
    assert set(parsed.schemas) == {"First"}


# ---------------------------------------------------------------------------
# 6 - the shipped file, shapes only, skipped with a reason when absent
# ---------------------------------------------------------------------------


def test_the_real_usmap_accounts_for_its_own_length_exactly() -> None:
    """SHAPES ONLY. Asserts no name and prints nothing (non-negotiable 2).

    This is the control that keeps the derived grammar honest: a wrong inner
    grammar cannot land on a section-tag boundary by accident.

    STRENGTHENED 2026-08-15 (CS-404). The module docstring of
    clockspeed/save/usmap.py cites this test for three properties - landing
    exactly on a four-character ASCII tag, every property type byte in range,
    and every name index in bounds. It asserted NONE of them: the only inner
    assertion was ``body_consumed <= compressed_size``, a ``<=`` that any
    grammar stopping early satisfies. An adversarial pass mutated the LOADER's
    grammar nine ways and eight still passed - dropping payload rows 8, 9 and
    24, mis-shaping row 8, reading slot as uint8, driving the entry loop on the
    property count, reading the enum name index as uint16, and setting
    MAX_KNOWN_PROPERTY_TYPE to 3. A cited fence that holds nothing is worse
    than no fence, because the citation is what stops anyone building one.
    """
    game_dir, _label = resolve_game_dir()
    if game_dir is None:
        pytest.skip("no game install resolved on this machine")
    path = game_dir / "CommunityResources" / "FactoryGame.usmap"
    if not path.is_file():
        pytest.skip("the install carries no FactoryGame.usmap")

    size_on_disk = path.stat().st_size
    raw = path.read_bytes()
    parsed = usmap.load_usmap(path)
    container = parsed.container

    assert container.magic == usmap.USMAP_MAGIC
    assert container.version >= usmap.VERSION_PACKAGE_VERSIONING
    assert container.compression_method == usmap.COMPRESSION_NONE
    assert container.compressed_size == container.decompressed_size
    assert container.header_size + container.compressed_size == size_on_disk

    # Shapes of the inner section, as counts only.
    assert len(parsed.names) > _ZERO
    assert len(parsed.schemas) > _ZERO
    assert parsed.body_consumed <= container.compressed_size

    # (1) THE WALK LANDS EXACTLY ON A FOUR-CHARACTER PRINTABLE ASCII TAG.
    # Bound as ints and a bool - never as bytes, which would put shipped
    # content into a failing assertion's repr.
    landing = container.header_size + parsed.body_consumed
    tag = raw[landing : landing + _TAG_WIDTH]
    assert len(tag) == _TAG_WIDTH
    assert all(_ASCII_SPACE <= byte < _ASCII_DELETE for byte in tag)
    # Strictly INSIDE the body: a walk that consumed everything, or that
    # stopped early enough to leave a second section unread, is not a landing.
    assert _ZERO < parsed.body_consumed < container.compressed_size

    # (2) EVERY PROPERTY TYPE BYTE IS IN RANGE, and (3) EVERY NAME INDEX IS IN
    # BOUNDS. The loader reports both as warnings rather than raising, so the
    # assertion is that neither warning was raised at all - which also rules
    # out a section that desynchronised and stopped short.
    codes = {warning.code for warning in parsed.warnings}
    assert usmap.WARN_UNKNOWN_PROPERTY_TYPE not in codes
    assert usmap.WARN_UNRESOLVED_NAME not in codes
    assert usmap.WARN_DESYNCHRONISED_SECTION not in codes
    # The one warning the shipped file DOES legitimately raise.
    assert codes == {usmap.WARN_TRAILING_SECTION}

    # Belt and braces on (2): assert the range directly rather than trusting
    # the absence of a warning to imply it.
    type_ids = {entry.type_id for schema in parsed.schemas.values() for entry in schema.properties}
    assert type_ids
    assert max(type_ids) <= usmap.MAX_KNOWN_PROPERTY_TYPE


# ---------------------------------------------------------------------------
# 6b - THE REBUILD AUDIT: the builder re-emits the shipped file's own bytes
#
# This is the strongest control in the module and the only one that closes the
# common-mode risk CS-404 exists for. Everything else compares the builder to a
# reader, or to another encoder, or to itself. This compares it to THE GAME.
#
# WHY THE LANDING ORACLE IS NOT ENOUGH, CONCRETELY. Writing a type-26
# descriptor's name index BEFORE its inner descriptor instead of after is
# wrong - it contradicts the shipped file in 3113 descriptors across 1873
# schemas - and it lands on the trailing tag at byte 1896914 exactly like the
# correct order, consuming identical bytes, because a u8-then-skip-4 read and a
# skip-4-then-u8 read cover the same five bytes. It passed the entire suite. No
# assertion built from synthetic bytes can see it, because with a small
# synthetic name index the low byte is itself a valid payload-free type id.
# Only the real file has name indices large enough to tell the two apart.
#
# WHY THE READER BELOW IS NOT CIRCULAR. It spells its own payload table rather
# than importing synthetic.USMAP_PROPERTY_PAYLOAD - the same "duplication IS
# the control" rule tests/save/test_synthetic.py uses for its independent
# reader - and it VALIDATES every index against the name table as it walks. A
# reader with the type-26 order wrong cannot complete the walk on the real
# file: it puts a name index outside the 57985-entry table. Measured.
#
# PRIVACY. Real names, and the whole shipped body, pass through the audit. So
# the audit CONTAINS ITS OWN EXCEPTIONS and returns integers: pytest renders
# the arguments of every frame in a failing traceback, so an escaping exception
# would put shipped content into the log. Nothing here binds a name, a byte
# string or a path into anything pytest can reach.
# ---------------------------------------------------------------------------

#: Spelled AGAIN, deliberately, rather than imported from the builder. See above.
_AUDIT_PAYLOAD: dict[int, tuple[int, bool]] = {
    8: (1, False),
    9: (0, True),
    24: (2, False),
    25: (1, False),
    26: (1, True),
}


@dataclass(frozen=True)
class _RebuildAudit:
    """The audit result. Every field is an int, a bool or a fixed token."""

    names: int
    enums: int
    enums_identical: int
    schemas: int
    schemas_identical: int
    schemas_count_split: int
    schemas_unexplained: int
    consumed: int
    trailing: int
    lands_on_printable_tag: bool
    failure: str


class _BodyCursor:
    """A minimal validating cursor over the shipped body.

    Deliberately NOT ``clockspeed.save.usmap._Reader``: reusing the loader's
    reader would make this audit a restatement of the loader's opinion, and the
    audit exists to grade the BUILDER against the GAME with the loader out of
    the loop entirely.
    """

    def __init__(self, body: bytes) -> None:
        """Wrap the body and start at zero."""
        self.body = body
        self.at = 0
        self.names: list[str] = []

    def u8(self) -> int:
        """Read an unsigned byte."""
        self.at += 1
        return self.body[self.at - 1]

    def u16(self) -> int:
        """Read an unsigned 16-bit integer."""
        self.at += 2
        return int(struct.unpack_from("<H", self.body, self.at - 2)[0])

    def u32(self) -> int:
        """Read an unsigned 32-bit integer."""
        self.at += 4
        return int(struct.unpack_from("<I", self.body, self.at - 4)[0])

    def checked(self, index: int) -> str:
        """Resolve a name index, REFUSING one out of bounds.

        This refusal is what makes the reader independent rather than circular.
        A reader with the type-26 field order wrong cannot get through the real
        file: it lands a name index outside the table and raises here.
        """
        if not 0 <= index < len(self.names):
            raise IndexError
        return self.names[index]


def _audit_read_names(cursor: _BodyCursor) -> None:
    """Read the name table into the cursor."""
    for _ in range(cursor.u32()):
        length = cursor.u8()
        cursor.names.append(cursor.body[cursor.at : cursor.at + length].decode("utf-8", "replace"))
        cursor.at += length


def _audit_enums(cursor: _BodyCursor, table: Mapping[str, int]) -> tuple[int, int]:
    """Rebuild every enum and compare bytes. Returns (total, identical)."""
    total = cursor.u32()
    identical = 0
    for _ in range(total):
        start = cursor.at
        name = cursor.checked(cursor.u32())
        members = [cursor.checked(cursor.u32()) for _ in range(cursor.u8())]
        if synthetic.build_usmap_enum_entry(name, members, table) == cursor.body[start : cursor.at]:
            identical += 1
    return total, identical


def _audit_descriptor(cursor: _BodyCursor, type_id: int, depth: int = 0) -> synthetic.UsmapType:
    """Read one property-type descriptor, inner descriptors before the name."""
    if depth > _MAX_AUDIT_DEPTH:
        raise RecursionError
    inner_count, has_name = _AUDIT_PAYLOAD.get(type_id, (0, False))
    inner = tuple(_audit_descriptor(cursor, cursor.u8(), depth + 1) for _ in range(inner_count))
    name = cursor.checked(cursor.u32()) if has_name else None
    return synthetic.UsmapType(type_id, name=name, inner=inner)


def _audit_one_schema(cursor: _BodyCursor, table: Mapping[str, int]) -> tuple[bool, bool]:
    """Rebuild one schema. Returns (byte identical, counts disagree)."""
    start = cursor.at
    name = cursor.checked(cursor.u32())
    raw_super = cursor.u32()
    declared = cursor.u16()
    serializable = cursor.u16()

    properties: list[tuple[str, int | synthetic.UsmapType]] = []
    for _ in range(serializable):
        cursor.u16()
        array_size = cursor.u8()
        property_name = cursor.checked(cursor.u32())
        shape = _audit_descriptor(cursor, cursor.u8())
        properties.append(
            (property_name, synthetic.UsmapType(shape.type_id, shape.name, shape.inner, array_size))
        )

    rebuilt = synthetic.build_usmap_schema_entry(
        synthetic.UsmapSchema(
            name=name,
            super_name=None if raw_super == _ALL_BITS_SET else cursor.checked(raw_super),
            properties=tuple(properties),
        ),
        table,
    )
    return rebuilt == cursor.body[start : cursor.at], declared != serializable


def _audit_rebuild(data: bytes, header_size: int, body_size: int) -> _RebuildAudit:
    """Rebuild every real enum and schema through the builder and compare bytes.

    CONTAINS EVERY EXCEPTION IT CAN RAISE and reports the TYPE NAME only, never
    a message. Real names and the whole shipped body pass through the frames
    below, and pytest renders the arguments of every frame in a failing
    traceback - so an escaping exception would put shipped content in the log.
    """
    totals = dict.fromkeys(
        (
            "names",
            "enums",
            "enums_identical",
            "schemas",
            "schemas_identical",
            "schemas_count_split",
            "schemas_unexplained",
            "consumed",
            "trailing",
        ),
        0,
    )
    landed = False
    failure = ""
    try:
        cursor = _BodyCursor(data[header_size : header_size + body_size])
        _audit_read_names(cursor)
        totals["names"] = len(cursor.names)
        table = synthetic.usmap_name_table(cursor.names)

        totals["enums"], totals["enums_identical"] = _audit_enums(cursor, table)

        totals["schemas"] = cursor.u32()
        for _ in range(totals["schemas"]):
            identical, counts_disagree = _audit_one_schema(cursor, table)
            if identical:
                totals["schemas_identical"] += 1
            elif counts_disagree:
                totals["schemas_count_split"] += 1
            else:
                totals["schemas_unexplained"] += 1

        totals["consumed"] = cursor.at
        totals["trailing"] = len(cursor.body) - cursor.at
        tag = cursor.body[cursor.at : cursor.at + _TAG_WIDTH]
        landed = len(tag) == _TAG_WIDTH and all(
            _ASCII_SPACE <= byte < _ASCII_DELETE for byte in tag
        )
    except Exception as exc:
        failure = type(exc).__name__

    return _RebuildAudit(lands_on_printable_tag=landed, failure=failure, **totals)


def test_the_builder_reproduces_the_shipped_bytes_it_models() -> None:
    """COUNTS ONLY, skip-if-absent. The control that grades the builder by the game.

    Kills the type-26 field-order mutant, which every other test in this repo
    passes. See the section comment for why nothing built from synthetic bytes
    can.
    """
    game_dir, _label = resolve_game_dir()
    if game_dir is None:
        pytest.skip("no game install resolved on this machine")
    path = game_dir / "CommunityResources" / "FactoryGame.usmap"
    if not path.is_file():
        pytest.skip("the install carries no FactoryGame.usmap")

    parsed = usmap.load_usmap(path)
    audit = _audit_rebuild(
        path.read_bytes(), parsed.container.header_size, parsed.container.compressed_size
    )

    assert audit.failure == ""
    assert audit.lands_on_printable_tag
    assert audit.consumed == parsed.body_consumed
    assert audit.trailing > _ZERO

    # EVERY enum re-emits byte-identically. No exceptions are tolerated here.
    assert audit.enums > _ZERO
    assert audit.enums_identical == audit.enums

    # Every schema re-emits byte-identically EXCEPT those the builder
    # structurally cannot express, and that shortfall is counted rather than
    # waved at. See synthetic.UsmapSchema.
    assert audit.schemas > _ZERO
    assert audit.schemas_unexplained == _ZERO
    assert audit.schemas_identical + audit.schemas_count_split == audit.schemas
    # The builder models the overwhelming majority - a regression that broke
    # most schemas while keeping the sum consistent would still be caught.
    assert audit.schemas_identical > audit.schemas_count_split


def test_the_evidence_table_matches_what_the_rebuild_audit_measures() -> None:
    """The recorded basis for the two REBUILD claims is not decoration."""
    game_dir, _label = resolve_game_dir()
    if game_dir is None:
        pytest.skip("no game install resolved on this machine")
    path = game_dir / "CommunityResources" / "FactoryGame.usmap"
    if not path.is_file():
        pytest.skip("the install carries no FactoryGame.usmap")

    parsed = usmap.load_usmap(path)
    audit = _audit_rebuild(
        path.read_bytes(), parsed.container.header_size, parsed.container.compressed_size
    )
    rebuilt = [
        item for item in synthetic.USMAP_EVIDENCE if item.basis == synthetic.USMAP_BASIS_REBUILD
    ]

    assert audit.failure == ""
    # Each REBUILD row cites a count. Those counts must be the ones measured
    # here, or the table is prose wearing a dataclass.
    assert str(audit.enums) in " ".join(item.detail for item in rebuilt)
    assert str(audit.schemas_identical) in " ".join(item.detail for item in rebuilt)
    assert str(audit.schemas) in " ".join(item.detail for item in rebuilt)
    assert str(audit.schemas_count_split) in " ".join(item.detail for item in rebuilt)


# ---------------------------------------------------------------------------
# 7 - the cache is actually a cache
# ---------------------------------------------------------------------------


def test_a_second_cached_usmap_call_does_not_reparse(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Proven with a call counter, not with a stopwatch."""
    community = tmp_path / "CommunityResources"
    community.mkdir()
    (community / "FactoryGame.usmap").write_bytes(
        synthetic.build_usmap(names=["Alpha", "Beta"], enums=[], schemas=[])
    )
    monkeypatch.setenv(ENV_GAME_DIR, str(tmp_path))
    monkeypatch.setenv(ENV_LOCAL_CONFIG, str(tmp_path / "absent.json"))
    usmap.clear_cache()

    calls: list[bytes] = []
    real_parse = usmap.parse_usmap

    def counting_parse(data: bytes) -> usmap.PropertyMap:
        calls.append(data)
        return real_parse(data)

    monkeypatch.setattr(usmap, "parse_usmap", counting_parse)

    first = usmap.cached_usmap()
    second = usmap.cached_usmap()

    assert first is not None
    assert first is second
    assert len(calls) == _ONE
    assert first.names == ("Alpha", "Beta")


def test_clear_cache_forces_a_reparse(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    community = tmp_path / "CommunityResources"
    community.mkdir()
    (community / "FactoryGame.usmap").write_bytes(
        synthetic.build_usmap(names=["Alpha"], enums=[], schemas=[])
    )
    monkeypatch.setenv(ENV_GAME_DIR, str(tmp_path))
    monkeypatch.setenv(ENV_LOCAL_CONFIG, str(tmp_path / "absent.json"))
    usmap.clear_cache()

    calls: list[bytes] = []
    real_parse = usmap.parse_usmap

    def counting_parse(data: bytes) -> usmap.PropertyMap:
        calls.append(data)
        return real_parse(data)

    monkeypatch.setattr(usmap, "parse_usmap", counting_parse)

    usmap.cached_usmap()
    usmap.clear_cache()
    usmap.cached_usmap()

    assert len(calls) == _TWO


def test_the_cache_notices_a_changed_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A patched install must not be served from a stale cache entry."""
    community = tmp_path / "CommunityResources"
    community.mkdir()
    target = community / "FactoryGame.usmap"
    target.write_bytes(synthetic.build_usmap(names=["Alpha"], enums=[], schemas=[]))
    monkeypatch.setenv(ENV_GAME_DIR, str(tmp_path))
    monkeypatch.setenv(ENV_LOCAL_CONFIG, str(tmp_path / "absent.json"))
    usmap.clear_cache()

    before = usmap.cached_usmap()
    target.write_bytes(
        synthetic.build_usmap(names=["Alpha", "Beta", "Gamma"], enums=[], schemas=[])
    )
    after = usmap.cached_usmap()

    assert before is not None
    assert after is not None
    assert len(before.names) == _ONE
    assert len(after.names) == _THREE


# ---------------------------------------------------------------------------
# Error taxonomy
# ---------------------------------------------------------------------------


def test_no_exception_carries_a_decoded_name_a_raw_byte_or_a_path(
    tmp_path: Path,
) -> None:
    """Field, offset, count, version or method integer, and a fixed reason. No more."""
    must_not_escape = "NameThatMustNotEscape"
    body = _shipped_body(
        names=[must_not_escape, "SynthSchema"],
        enums=[],
        schemas=[("SynthSchema", None, [(must_not_escape, _TYPE_INT)])],
    )
    framed = _reframe(synthetic.build_usmap(names=[], enums=[], schemas=[]), body)

    messages: list[str] = []
    for truncation in range(12, len(framed)):
        try:
            usmap.parse_usmap(framed[:truncation])
        except usmap.UsmapError as exc:
            messages.append(str(exc))
    try:
        usmap.parse_usmap(synthetic.usmap_with_compression(1))
    except usmap.UsmapError as exc:
        messages.append(str(exc))
    try:
        usmap.load_usmap(tmp_path / "CommunityResources" / "FactoryGame.usmap")
    except usmap.UsmapError as exc:
        messages.append(str(exc))

    assert messages
    for message in messages:
        assert must_not_escape not in message
        assert message.isascii()
        assert "\\" not in message
        assert ":/" not in message.replace("://", "")
        assert "0x" not in message
        assert str(tmp_path) not in message


def test_the_error_hierarchy_is_rooted_at_usmap_error() -> None:
    assert issubclass(usmap.UsmapFormatError, usmap.UsmapError)
    assert issubclass(usmap.UnsupportedUsmapCompressionError, usmap.UsmapError)
    assert not issubclass(usmap.UnsupportedUsmapCompressionError, usmap.UsmapFormatError)


# ---------------------------------------------------------------------------
# 8 - CS-404 part 2: the builder's own shipped-grammar mode
#
# THE ORACLE for every test below is the REAL loader, not a second opinion in
# this file. A body the builder produces in shipped mode must load through
# clockspeed/save/usmap.py and yield back exactly what went in, consuming the
# body to its final byte. A grammar that is wrong anywhere does not land on the
# exact end by accident.
#
# The reason this mode exists at all: build_usmap's enum and schema sections
# wrote inline length-prefixed strings and no property-type byte, so no fixture
# in the corpus had ever exercised the loader's real inner grammar. The tests
# above worked around it with a hand-built body in THIS file, which is a corpus
# that can only ever agree with whoever wrote it.
# ---------------------------------------------------------------------------


def test_the_builders_shipped_mode_round_trips_through_the_real_loader() -> None:
    """THE decisive control: what goes in comes back, and the body ends exactly.

    ``body_consumed == compressed_size`` is the assertion that cannot be passed
    by a grammar that is wrong somewhere and self-consistent - a misencoded
    section leaves the cursor short or runs it off the end.
    """
    names = ["Alpha", "Beta", "ESynthEnum", "Member0", "Member1", "SynthSchema", "SynthBase"]
    blob = synthetic.build_usmap(
        names=names,
        enums=[("ESynthEnum", ["Member0", "Member1"])],
        schemas=[
            synthetic.UsmapSchema(
                name="SynthSchema",
                super_name="SynthBase",
                properties=(("Alpha", _TYPE_INT), ("Beta", _TYPE_BOOL)),
            )
        ],
        shipped=True,
    )

    parsed = usmap.parse_usmap(blob)

    assert parsed.names == tuple(names)
    assert parsed.enums == {"ESynthEnum": ("Member0", "Member1")}
    assert set(parsed.schemas) == {"SynthSchema"}
    schema = parsed.schemas["SynthSchema"]
    assert schema.super_name == "SynthBase"
    assert [entry.name for entry in schema.properties] == ["Alpha", "Beta"]
    assert [entry.type_id for entry in schema.properties] == [_TYPE_INT, _TYPE_BOOL]
    assert [entry.slot for entry in schema.properties] == [_ZERO, _ONE]
    assert parsed.warnings == ()
    assert parsed.body_consumed == parsed.container.compressed_size


def test_the_shipped_mode_writes_a_uint32_name_index_where_legacy_wrote_a_string() -> None:
    """The exact defect CS-404 part 2 closes, asserted at the byte level.

    The enum's name is a uint32 index into the name table. The legacy grammar
    wrote a uint8 length followed by the characters, which is what made the
    loader read a member index off the end of the file.
    """
    blob = synthetic.build_usmap(
        names=["ESynthEnum", "Member0"],
        enums=[("ESynthEnum", ["Member0"])],
        schemas=[],
        shipped=True,
    )
    body = blob[_HEADER_NO_VERSIONING:]

    # names: count, then one uint8 length plus that many bytes, twice.
    at = 4 + (1 + len("ESynthEnum")) + (1 + len("Member0"))
    (enum_count,) = struct.unpack_from("<I", body, at)
    (enum_name_index,) = struct.unpack_from("<I", body, at + 4)
    (member_count,) = struct.unpack_from("<B", body, at + 8)
    (member_index,) = struct.unpack_from("<I", body, at + 9)

    assert enum_count == _ONE
    assert enum_name_index == _ZERO
    assert member_count == _ONE
    assert member_index == _ONE
    assert len(body) == at + 13 + 4


def test_a_shipped_schema_with_no_super_writes_the_all_bits_set_sentinel() -> None:
    """Asserted on the BYTES, because the parsed model cannot tell the difference.

    ``super_name is None`` alone does NOT prove the sentinel was written: the
    loader maps ANY unresolvable super index to None
    (clockspeed/save/usmap.py:670), so a builder writing 0x0000FFFF instead of
    0xFFFFFFFF would produce an identical PropertyMap. That mutation was run
    against an earlier version of this test and survived it - the assertion has
    to reach the encoding itself.
    """
    names = ["Alpha", "SynthSchema"]
    blob = synthetic.build_usmap(
        names=names,
        enums=[],
        schemas=[
            synthetic.UsmapSchema(name="SynthSchema", properties=(("Alpha", _TYPE_INT),)),
        ],
        shipped=True,
    )
    body = blob[_HEADER_NO_VERSIONING:]

    # name count, both names, enum count, schema count, then the schema's own
    # name index - the super index is the uint32 after that.
    at = 4 + sum(1 + len(text) for text in names) + 4 + 4 + 4
    (raw_super,) = struct.unpack_from("<I", body, at)
    parsed = usmap.parse_usmap(blob)

    assert raw_super == synthetic.USMAP_NO_SUPER
    assert raw_super == _ALL_BITS_SET
    assert parsed.schemas["SynthSchema"].super_name is None
    assert parsed.body_consumed == parsed.container.compressed_size


def _descriptor(shape: str) -> synthetic.UsmapType:
    """Build one payload-carrying descriptor by name.

    Kept out of the ``parametrize`` list on purpose: a decorator argument is
    evaluated at COLLECTION time, so constructing these there turns any problem
    with the type into a collection error that hides every other test in the
    module behind it.
    """
    inner_int = synthetic.UsmapType(_TYPE_INT)
    shapes = {
        "struct": synthetic.UsmapType(_TYPE_STRUCT, name="SynthBase"),
        "array": synthetic.UsmapType(_TYPE_ARRAY, inner=(inner_int,)),
        "set": synthetic.UsmapType(_TYPE_SET, inner=(synthetic.UsmapType(_TYPE_BOOL),)),
        "map": synthetic.UsmapType(_TYPE_MAP, inner=(inner_int, synthetic.UsmapType(_TYPE_BOOL))),
        "enum": synthetic.UsmapType(_TYPE_ENUM_PROPERTY, name="SynthBase", inner=(inner_int,)),
    }
    return shapes[shape]


@pytest.mark.parametrize(
    ("shape", "expected_type"),
    [
        ("struct", _TYPE_STRUCT),
        ("array", _TYPE_ARRAY),
        ("set", _TYPE_SET),
        ("map", _TYPE_MAP),
        ("enum", _TYPE_ENUM_PROPERTY),
    ],
)
def test_every_payload_carrying_property_type_round_trips(shape: str, expected_type: int) -> None:
    """The four payload shapes measured on the shipped file, one test each.

    A builder that wrote the type byte and omitted its payload would leave the
    loader reading the NEXT entry's bytes as this one's, which is the exact
    class of silently-wrong fixture CS-404 exists to remove.
    """
    blob = synthetic.build_usmap(
        names=["Alpha", "SynthSchema", "SynthBase", "Tail"],
        enums=[],
        schemas=[
            synthetic.UsmapSchema(
                name="SynthSchema",
                properties=(("Alpha", _descriptor(shape)), ("Tail", _TYPE_BOOL)),
            ),
        ],
        shipped=True,
    )

    parsed = usmap.parse_usmap(blob)

    schema = parsed.schemas["SynthSchema"]
    assert [entry.name for entry in schema.properties] == ["Alpha", "Tail"]
    assert schema.properties[0].type_id == expected_type
    # The entry AFTER the payload-carrying one is the real check: it can only
    # be read correctly if the payload width was written correctly.
    assert schema.properties[1].type_id == _TYPE_BOOL
    assert parsed.warnings == ()
    assert parsed.body_consumed == parsed.container.compressed_size


def test_a_nested_descriptor_round_trips_through_the_real_loader() -> None:
    """An array of structs: the inner descriptor itself carries a payload."""
    blob = synthetic.build_usmap(
        names=["Alpha", "SynthSchema", "SynthBase", "Tail"],
        enums=[],
        schemas=[
            synthetic.UsmapSchema(
                name="SynthSchema",
                properties=(
                    (
                        "Alpha",
                        synthetic.UsmapType(
                            _TYPE_ARRAY,
                            inner=(synthetic.UsmapType(_TYPE_STRUCT, name="SynthBase"),),
                        ),
                    ),
                    ("Tail", _TYPE_BOOL),
                ),
            ),
        ],
        shipped=True,
    )

    parsed = usmap.parse_usmap(blob)

    schema = parsed.schemas["SynthSchema"]
    assert [entry.type_id for entry in schema.properties] == [_TYPE_ARRAY, _TYPE_BOOL]
    assert parsed.body_consumed == parsed.container.compressed_size


def test_a_declared_array_size_round_trips() -> None:
    """The shipped file carries fixed arrays wider than one."""
    width = 4
    blob = synthetic.build_usmap(
        names=["Alpha", "SynthSchema"],
        enums=[],
        schemas=[
            synthetic.UsmapSchema(
                name="SynthSchema",
                properties=(("Alpha", synthetic.UsmapType(_TYPE_INT, array_size=width)),),
            ),
        ],
        shipped=True,
    )

    parsed = usmap.parse_usmap(blob)

    assert parsed.schemas["SynthSchema"].properties[0].array_size == width


# --- the builder refuses to emit a fixture it knows is desynchronised -------


def test_the_builder_refuses_a_payload_carrying_type_with_no_descriptor() -> None:
    """Writing type 9 with no name index would desynchronise the whole section.

    Refusing is the point: a builder that emitted it would produce a fixture
    that is wrong in exactly the way no test in the corpus could see.
    """
    with pytest.raises(ValueError, match="descriptor"):
        synthetic.build_usmap(
            names=["Alpha", "SynthSchema"],
            enums=[],
            schemas=[
                synthetic.UsmapSchema(name="SynthSchema", properties=(("Alpha", _TYPE_STRUCT),)),
            ],
            shipped=True,
        )


def test_the_builder_refuses_a_wrong_inner_descriptor_count() -> None:
    """A map takes a key AND a value descriptor. One is not enough."""
    with pytest.raises(ValueError, match="descriptor"):
        synthetic.build_usmap(
            names=["Alpha", "SynthSchema"],
            enums=[],
            schemas=[
                synthetic.UsmapSchema(
                    name="SynthSchema",
                    properties=(
                        ("Alpha", synthetic.UsmapType(_TYPE_MAP, inner=(synthetic.UsmapType(1),))),
                    ),
                ),
            ],
            shipped=True,
        )


def test_the_builder_refuses_a_name_that_is_not_in_the_name_table() -> None:
    """Shipped mode writes indices, so an absent name has no index to write."""
    with pytest.raises(ValueError, match="name table"):
        synthetic.build_usmap(
            names=["Alpha"],
            enums=[("AbsentEnum", ["Alpha"])],
            schemas=[],
            shipped=True,
        )


def test_the_builder_accepts_an_unknown_type_and_the_loader_flags_and_skips_it() -> None:
    """RENAMED 2026-08-15: the old name said "refuses" and proved the opposite.

    There is no ``pytest.raises`` here and there should not be. An unknown type
    carries no payload the builder can get wrong, so emitting it is safe, and
    the loader flagging and skipping it is exactly non-negotiable 7 working. The
    old name stated the opposite of what the body asserts.
    """
    blob = synthetic.build_usmap(
        names=["Alpha", "SynthSchema", "Tail"],
        enums=[],
        schemas=[
            synthetic.UsmapSchema(
                name="SynthSchema",
                properties=(("Alpha", _UNKNOWN_TYPE), ("Tail", _TYPE_BOOL)),
            ),
        ],
        shipped=True,
    )

    parsed = usmap.parse_usmap(blob)

    assert usmap.WARN_UNKNOWN_PROPERTY_TYPE in [w.code for w in parsed.warnings]
    assert [entry.name for entry in parsed.schemas["SynthSchema"].properties] == ["Tail"]
    assert parsed.body_consumed == parsed.container.compressed_size


# ---------------------------------------------------------------------------
# 9 - CS-404 part 2: the version-1 versioning block gets synthetic coverage
#
# Every branch below was dead on a machine with no game install before this
# item: build_usmap declared version 0, and the loader gates the whole block
# on version >= 1. CI has no install, so CI covered none of it.
# ---------------------------------------------------------------------------


def test_the_default_version_writes_no_versioning_block() -> None:
    """The additive constraint, asserted rather than assumed."""
    blob = synthetic.build_usmap(names=["Alpha"], enums=[], schemas=[])

    parsed = usmap.parse_usmap(blob)

    assert parsed.container.version == _VERSION_ZERO
    assert parsed.container.header_size == _HEADER_NO_VERSIONING


def test_a_version_one_usmap_that_declares_no_versioning_block_round_trips() -> None:
    """Version 1 with bHasVersioning 0: the second gate, on its own."""
    blob = synthetic.build_usmap(
        names=["Alpha"], enums=[], schemas=[], version=_VERSION_ONE, custom_versions=None
    )

    parsed = usmap.parse_usmap(blob)

    assert parsed.container.version == _VERSION_ONE
    assert parsed.container.header_size == _HEADER_VERSIONING_OFF
    assert parsed.names == ("Alpha",)
    assert parsed.warnings == ()


def test_a_version_one_usmap_with_a_versioning_block_round_trips() -> None:
    """Version 1 with bHasVersioning 1 and no custom version records."""
    blob = synthetic.build_usmap(
        names=["Alpha"], enums=[], schemas=[], version=_VERSION_ONE, custom_versions=0
    )

    parsed = usmap.parse_usmap(blob)

    assert parsed.container.version == _VERSION_ONE
    assert parsed.container.header_size == _HEADER_VERSIONING_ON
    assert parsed.names == ("Alpha",)
    assert parsed.warnings == ()


@pytest.mark.parametrize("records", [1, 2, 89])
def test_custom_version_records_are_walked_rather_than_assumed(records: int) -> None:
    """The header size is DERIVED by walking, so each record must move it by 20."""
    blob = synthetic.build_usmap(
        names=["Alpha"], enums=[], schemas=[], version=_VERSION_ONE, custom_versions=records
    )

    parsed = usmap.parse_usmap(blob)

    expected = _HEADER_VERSIONING_ON + records * _CUSTOM_VERSION_RECORD_BYTES
    assert parsed.container.header_size == expected
    assert parsed.container.header_size + parsed.container.compressed_size == len(blob)
    assert parsed.names == ("Alpha",)


def test_a_version_above_the_known_maximum_is_flagged_and_still_parses() -> None:
    """Non-negotiable 7: unknown content is flagged and skipped, never fatal.

    This warning code had no test before CS-404 - nothing in the corpus could
    build a usmap declaring a version at all.
    """
    blob = synthetic.build_usmap(
        names=["Alpha"], enums=[], schemas=[], version=_VERSION_UNKNOWN, custom_versions=0
    )

    parsed = usmap.parse_usmap(blob)

    assert usmap.WARN_UNKNOWN_VERSION in [w.code for w in parsed.warnings]
    assert parsed.names == ("Alpha",)


def test_a_negative_custom_version_count_is_a_format_error() -> None:
    """The declared count is written verbatim, so the range check is reachable."""
    blob = synthetic.build_usmap(
        names=["Alpha"], enums=[], schemas=[], version=_VERSION_ONE, custom_versions=-1
    )

    with pytest.raises(usmap.UsmapFormatError) as caught:
        usmap.parse_usmap(blob)

    assert caught.value.field == "custom_version_count"


def test_a_custom_version_count_above_the_ceiling_is_a_format_error() -> None:
    blob = synthetic.build_usmap(
        names=["Alpha"],
        enums=[],
        schemas=[],
        version=_VERSION_ONE,
        custom_versions=_CUSTOM_VERSION_CEILING + 1,
    )

    with pytest.raises(usmap.UsmapFormatError) as caught:
        usmap.parse_usmap(blob)

    assert caught.value.field == "custom_version_count"


@pytest.mark.parametrize("records", [0, 1, 3])
def test_every_byte_of_the_versioning_block_is_non_zero(records: int) -> None:
    """The stated rationale for non-zero filler, made machine-checked.

    synthetic.py justifies non-zero sentinels by saying a misaligned skip would
    otherwise read its compression-method byte as 0 - the one value that parses
    - and succeed silently with garbage sizes. Nothing exercised that, and the
    custom version records were in fact zero-filled, so the rationale covered 12
    bytes and failed for the 20N that dominate the block. Three separate
    mutations zeroing the sentinels, and one filling the records with 0xFF, all
    survived the suite before this test existed.
    """
    blob = synthetic.build_usmap(
        names=["Alpha"], enums=[], schemas=[], version=_VERSION_ONE, custom_versions=records
    )
    payload = records * _CUSTOM_VERSION_RECORD_BYTES

    # ONLY the regions a reader SKIPS. bHasVersioning and the record count are
    # meaningful small integers and legitimately carry zero bytes; claiming the
    # whole block is non-zero would be a claim that cannot be true.
    skipped = (
        blob[7:15]  # file_version_ue4, file_version_ue5
        + blob[19 : 19 + payload]  # the custom version records
        + blob[19 + payload : 23 + payload]  # network_compatible_changelist
    )

    assert len(skipped) == 12 + payload
    assert all(byte != _ZERO for byte in skipped), "skipped filler must be non-zero"
    # NOT asserted: which non-zero byte. Changing the record filler from 0x5F
    # to 0xFF survives this test and every other, and that is correct rather
    # than a gap - the stated property is "non-zero so a misaligned skip reads
    # a method byte that cannot parse", and 0xFF satisfies it exactly as well.
    # Pinning the literal would make an arbitrary choice load-bearing and would
    # turn a free implementation detail into a false constraint.
    # And the method byte really is the one immediately after the block, which
    # is what makes a misaligned skip land in the filler rather than past it.
    assert blob[23 + payload] == usmap.COMPRESSION_NONE
    assert usmap.parse_usmap(blob).container.header_size == _HEADER_VERSIONING_ON + payload


def test_a_misaligned_skip_into_the_versioning_block_is_refused_not_accepted() -> None:
    """Why the filler is non-zero, demonstrated end to end.

    Understating the declared record count leaves the loader reading its method
    byte from inside the filler. Non-zero filler makes that a clean refusal.
    """
    records = 2
    blob = bytearray(
        synthetic.build_usmap(
            names=["Alpha"],
            enums=[],
            schemas=[],
            version=_VERSION_ONE,
            custom_versions=records,
        )
    )
    # Understate the count by one, so the loader stops 20 bytes early.
    struct.pack_into("<i", blob, 15, records - 1)

    with pytest.raises(usmap.UsmapError) as caught:
        usmap.parse_usmap(bytes(blob))

    # Refused on the nonsense method, NOT silently parsed with garbage sizes.
    assert isinstance(caught.value, usmap.UnsupportedUsmapCompressionError)
    assert caught.value.method != usmap.COMPRESSION_NONE


def test_a_versioned_header_still_carries_a_shipped_grammar_body() -> None:
    """The two new capabilities compose - this is the shape of the real file."""
    blob = synthetic.build_usmap(
        names=["Alpha", "ESynthEnum", "Member0", "SynthSchema"],
        enums=[("ESynthEnum", ["Member0"])],
        schemas=[
            synthetic.UsmapSchema(name="SynthSchema", properties=(("Alpha", _TYPE_INT),)),
        ],
        shipped=True,
        version=_VERSION_ONE,
        custom_versions=3,
    )

    parsed = usmap.parse_usmap(blob)

    assert parsed.container.version == _VERSION_ONE
    assert parsed.enums == {"ESynthEnum": ("Member0",)}
    assert set(parsed.schemas) == {"SynthSchema"}
    assert parsed.warnings == ()
    assert parsed.body_consumed == parsed.container.compressed_size


# ---------------------------------------------------------------------------
# 10 - reconciliation against the hand-built body this file used to carry
#
# Two independently written encoders of the same measured grammar agreeing byte
# for byte is a weaker signal than the round trip above - both could be wrong
# the same way - but a DISAGREEMENT would be decisive, so the check is kept.
# ---------------------------------------------------------------------------


def test_the_builders_shipped_mode_agrees_with_the_hand_built_body_byte_for_byte() -> None:
    names = ["Alpha", "Beta", "ESynthEnum", "Member0", "Member1", "SynthSchema", "SynthBase"]
    hand_built = _shipped_body(
        names=names,
        enums=[("ESynthEnum", ["Member0", "Member1"])],
        schemas=[("SynthSchema", "SynthBase", [("Alpha", _TYPE_INT), ("Beta", _TYPE_BOOL)])],
    )

    from_builder = synthetic.build_usmap_body(
        names=names,
        enums=[("ESynthEnum", ["Member0", "Member1"])],
        schemas=[
            synthetic.UsmapSchema(
                name="SynthSchema",
                super_name="SynthBase",
                properties=(("Alpha", _TYPE_INT), ("Beta", _TYPE_BOOL)),
            )
        ],
        shipped=True,
    )

    assert from_builder == hand_built


def test_the_builders_shipped_body_frames_to_the_same_bytes_as_reframe() -> None:
    """The builder frames a body exactly as this module's own _reframe does.

    So every ``_reframe(_shipped_body(...))`` call site above could be moved
    onto ``build_usmap(shipped=True)`` without changing a single byte.
    """
    body = synthetic.build_usmap_body(
        names=["Alpha", "SynthSchema"],
        enums=[],
        schemas=[
            synthetic.UsmapSchema(name="SynthSchema", properties=(("Alpha", _TYPE_INT),)),
        ],
        shipped=True,
    )
    framed = _reframe(synthetic.build_usmap(names=[], enums=[], schemas=[]), body)

    direct = synthetic.build_usmap(
        names=["Alpha", "SynthSchema"],
        enums=[],
        schemas=[
            synthetic.UsmapSchema(name="SynthSchema", properties=(("Alpha", _TYPE_INT),)),
        ],
        shipped=True,
    )

    assert direct == framed


def test_the_loader_never_writes_to_the_install(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Non-negotiable 1: the game install is opened read-only, always."""
    community = tmp_path / "CommunityResources"
    community.mkdir()
    target = community / "FactoryGame.usmap"
    payload = synthetic.build_usmap(names=["Alpha"], enums=[], schemas=[])
    target.write_bytes(payload)
    monkeypatch.setenv(ENV_GAME_DIR, str(tmp_path))
    monkeypatch.setenv(ENV_LOCAL_CONFIG, str(tmp_path / "absent.json"))
    usmap.clear_cache()

    before = sorted(p.name for p in community.iterdir())
    usmap.cached_usmap()

    assert target.read_bytes() == payload
    assert sorted(p.name for p in community.iterdir()) == before
