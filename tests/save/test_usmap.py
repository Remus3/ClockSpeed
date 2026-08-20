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

import ast
import importlib
import re
import struct
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

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
    """Read the name table into the cursor, REFUSING a name that does not decode.

    The refusal is the same independence :meth:`_BodyCursor.checked` buys, one
    field over, and CS-435 is what made it necessary. Decoding with
    ``errors="replace"`` here would be a FALSE GREEN rather than a leftover:
    :func:`_audit_rebuild` builds its index table from ITS OWN names, so a
    substituted name resolves to the index the file actually holds, the rebuilt
    entry matches byte for byte, and the audit reports IDENTICAL for a name it
    never read. Measured on a synthetic body carrying one undecodable name:
    ``errors="replace"`` returns one enum counted IDENTICAL and an empty
    ``failure``; strict returns ``failure="UnicodeDecodeError"`` and counts
    nothing. Both install-backed tests that consume :func:`_audit_rebuild` would
    otherwise be grading the builder against a substitution.

    A raise is contained by :func:`_audit_rebuild`, which reports the exception
    TYPE NAME and never its message - and a ``UnicodeDecodeError`` message
    quotes the offending bytes, so that containment is an echo-path control
    rather than tidiness.
    """
    for _ in range(cursor.u32()):
        length = cursor.u8()
        cursor.names.append(cursor.body[cursor.at : cursor.at + length].decode("utf-8"))
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
    """Asserted on the BYTES, because ``super_name`` alone cannot carry it.

    ``super_name is None`` does NOT prove the sentinel was written: None is
    also what an unresolvable index yields, so a builder writing 0x0000FFFF
    instead of 0xFFFFFFFF would produce the same ``super_name``. That mutation
    was run against an earlier version of this test and survived it - the
    assertion has to reach the encoding itself.

    UPDATED by CS-417, which made those two cases distinguishable through
    ``warnings`` rather than through ``super_name``. This test is deliberately
    NOT rewritten onto that signal: asserting the bytes keeps it a check on
    what the BUILDER encodes, independent of what the loader reports, which is
    the whole reason it exists. The loader-side behaviour is covered by
    ``test_an_out_of_bounds_super_index_is_flagged_rather_than_read_as_no_super``.
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


# ---------------------------------------------------------------------------
# 7 - CS-417: an unresolvable super index is FLAGGED, not read as "no super"
#
# Non-negotiable 7 has two halves and these cover the SECOND one. "Never fatal"
# is easy to satisfy by accident - returning None for anything unreadable
# satisfies it. "Never silently wrong" has to be satisfied on purpose, because
# the failure renders as a success.
#
# The shipped file carries no out-of-bounds super index, so neither the landing
# oracle nor the rebuild audit above can reach this path. It is constructed.
# ---------------------------------------------------------------------------

#: An index no two-name table can resolve, and NOT the all-bits-set sentinel:
#: the sentinel's low half, which is the encoding mutation a 16-bit-narrowed
#: writer would produce.
_UNRESOLVABLE_INDEX = 0x0000FFFF

#: Bytes in the uint32 super index field.
_SUPER_INDEX_WIDTH = 4

#: Offsets of the schema's other two name indices, relative to the super index.
#: Name index (4), property count (2), serializable count (2), slot (2) and
#: array size (1) sit between the super index and the property's name index.
_SCHEMA_NAME_DELTA = -4
_PROPERTY_NAME_DELTA = 11

#: What ``_shipped_body`` writes at each of those three sites for the two-name
#: table below, asserted as the patch anchor.
_INDEX_OF_SYNTH_SCHEMA = 1
_INDEX_OF_ALPHA = 0


def _super_index_offset(names: list[str]) -> int:
    """Byte offset of the lone schema's super index inside a ``_shipped_body``.

    Name count, every name, the enum count, the schema count, then the schema's
    own name index - the super index is the uint32 after that. The same walk
    ``test_a_shipped_schema_with_no_super_writes_the_all_bits_set_sentinel``
    does, and it holds only for a body with one schema and no enums.
    """
    return 4 + sum(1 + len(text) for text in names) + 4 + 4 + 4


def _patched_body(names: list[str], at: int, value: int, anchor: int) -> bytes:
    """A one-schema body with the uint32 at ``at`` overwritten by ``value``.

    ``anchor`` is what that uint32 must hold BEFORE the overwrite, and it is
    asserted. A patch that lands on the wrong offset would otherwise leave
    every test built on it green while testing nothing - CONVENTIONS.md section
    7.2, "a mutation that fails to apply looks GREEN".
    """
    body = bytearray(
        _shipped_body(
            names=names,
            enums=[],
            schemas=[("SynthSchema", None, [("Alpha", _TYPE_INT)])],
        )
    )
    (found,) = struct.unpack_from("<I", body, at)
    assert found == anchor, f"byte {at} holds {found}, not the expected anchor {anchor}"
    struct.pack_into("<I", body, at, value)
    return bytes(body)


def test_an_out_of_bounds_super_index_is_flagged_rather_than_read_as_no_super() -> None:
    """CS-417. The two bodies differ ONLY inside the four-byte super index.

    One holds the all-bits-set sentinel that genuinely means "no super"; the
    other holds an index no two-name table can resolve. Both parse, and both
    leave ``super_name`` None, because None is the only thing either one could
    say - so whether the unresolvable one was FLAGGED is the entire difference
    between them.

    That is why both directions are asserted. A test that only checked the
    warning fires would pass just as happily against an implementation that
    warned on every schema, sentinel included, and that distinguishes nothing.
    """
    names = ["Alpha", "SynthSchema"]
    at = _super_index_offset(names)
    framing = synthetic.build_usmap(names=[], enums=[], schemas=[])
    genuine_body = _patched_body(names, at, _ALL_BITS_SET, _ALL_BITS_SET)
    unresolvable_body = _patched_body(names, at, _UNRESOLVABLE_INDEX, _ALL_BITS_SET)

    differing = {
        offset
        for offset, (left, right) in enumerate(zip(genuine_body, unresolvable_body, strict=True))
        if left != right
    }
    assert differing
    assert differing <= set(range(at, at + _SUPER_INDEX_WIDTH))

    genuine = usmap.parse_usmap(_reframe(framing, genuine_body))
    unresolvable = usmap.parse_usmap(_reframe(framing, unresolvable_body))

    # Neither parse can say anything but None about the super type ...
    assert genuine.schemas["SynthSchema"].super_name is None
    assert unresolvable.schemas["SynthSchema"].super_name is None
    # ... so the warnings are the only place the difference can show up.
    # The sentinel is silent: the negative control that gives the next
    # assertion its meaning.
    assert genuine.warnings == ()
    # And the unresolvable index is flagged, with the same code its two siblings
    # use and a subject naming which of the three sites failed. Asserted as what
    # IS there rather than as an absence.
    #
    # THE SUBJECT WAS THE BARE ``schema-0`` UNTIL CS-431, shared with the schema
    # name and the property name. Section 13 records what that cost; the change
    # here is the one line of this test it touched.
    assert [(warning.code, warning.subject) for warning in unresolvable.warnings] == [
        (usmap.WARN_UNRESOLVED_NAME, "schema-0-super")
    ]


def test_an_out_of_bounds_super_index_keeps_the_schema_and_its_properties() -> None:
    """Flagged and skipped, never FATAL - the first half of non-negotiable 7.

    Only the super type is unreadable. The schema's own name and every property
    resolve, so dropping the whole schema would discard readable content to
    report an unreadable field.
    """
    names = ["Alpha", "SynthSchema"]
    framing = synthetic.build_usmap(names=[], enums=[], schemas=[])
    body = _patched_body(names, _super_index_offset(names), _UNRESOLVABLE_INDEX, _ALL_BITS_SET)

    parsed = usmap.parse_usmap(_reframe(framing, body))

    schema = parsed.schemas["SynthSchema"]
    assert schema.name == "SynthSchema"
    assert [entry.name for entry in schema.properties] == ["Alpha"]
    assert parsed.body_consumed == parsed.container.compressed_size


@pytest.mark.parametrize(
    ("site", "delta", "anchor"),
    [
        ("schema-name", _SCHEMA_NAME_DELTA, _INDEX_OF_SYNTH_SCHEMA),
        ("super", 0, _ALL_BITS_SET),
        ("property-name", _PROPERTY_NAME_DELTA, _INDEX_OF_ALPHA),
    ],
)
def test_every_unresolvable_name_index_in_a_schema_raises_the_same_code(
    site: str, delta: int, anchor: int
) -> None:
    """Parity across the three name indices a schema entry carries.

    Before CS-417 the middle row was the odd one out: it mapped an unresolvable
    index to None and said nothing at all. Parametrized rather than written
    three times so that flagging one site and forgetting another goes red.
    """
    names = ["Alpha", "SynthSchema"]
    at = _super_index_offset(names) + delta
    framing = synthetic.build_usmap(names=[], enums=[], schemas=[])
    body = _patched_body(names, at, _UNRESOLVABLE_INDEX, anchor)

    parsed = usmap.parse_usmap(_reframe(framing, body))

    codes = {warning.code for warning in parsed.warnings}
    assert codes == {usmap.WARN_UNRESOLVED_NAME}, f"{site} at byte {at}"


# ---------------------------------------------------------------------------
# 8 - CS-416: __all__ agrees with the module, in BOTH directions
#
# The forward direction - every exported name exists - is the one that is
# usually written, and it is structurally incapable of catching a name that was
# defined and never exported: an ``__all__`` listing nothing at all satisfies
# it perfectly. The reverse direction is what found the three constants below.
#
# Consequence today is limited to ``from ... import *``, which nothing in this
# repo does, so this is inert rather than broken. It earns a test because
# ``__all__`` is the module's STATED public surface, and a stated surface that
# disagrees with the module is a claim that drifts silently.
# ---------------------------------------------------------------------------


def _module_level_public_names() -> tuple[list[str], list[str]]:
    """Public constants and public classes/functions bound at module level.

    Read from the SOURCE rather than from ``dir(usmap)``, and that choice is
    what makes this the reverse direction rather than a restatement of
    ``__all__``. ``dir()`` cannot tell a name the module DEFINES from one it
    merely imported, so a ``dir()``-based check would demand that ``Path``,
    ``Final`` and ``redact`` be exported too. An assignment is an ``Assign`` or
    an ``AnnAssign`` node; an import is neither, and neither is a ``def``.

    Reading as ASCII is a second, free assertion: non-negotiable 4 means this
    file cannot contain a byte above 0x7E, and a decode error here says so.

    Returns:
        ``(constants, definitions)``, each in source order.
    """
    source_path = usmap.__file__
    assert source_path is not None, "the module under test has no file on disk"
    tree = ast.parse(Path(source_path).read_text(encoding="ascii"))

    constants: list[str] = []
    definitions: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.AnnAssign | ast.Assign):
            targets = [node.target] if isinstance(node, ast.AnnAssign) else node.targets
            constants.extend(
                target.id
                for target in targets
                if isinstance(target, ast.Name) and not target.id.startswith("_")
            )
        elif isinstance(node, ast.ClassDef | ast.FunctionDef) and not node.name.startswith("_"):
            definitions.append(node.name)
    return constants, definitions


def test_every_public_module_level_constant_is_exported() -> None:
    """CS-416. The direction that catches a constant nobody exported.

    All three names this found - MAX_KNOWN_VERSION, USMAP_RELATIVE and
    WARN_UNKNOWN_VERSION - were defined beside constants that WERE exported,
    which is how they were missed: WARN_UNKNOWN_VERSION sits in the middle of
    the six-constant WARN_* block and was the only one of the six left out.
    """
    constants, _definitions = _module_level_public_names()

    assert constants, "the AST walk found no module-level constants at all"
    assert [name for name in constants if name not in usmap.__all__] == []


def test_every_public_class_and_function_is_exported() -> None:
    """The same direction over the other half of the public surface."""
    _constants, definitions = _module_level_public_names()

    assert definitions, "the AST walk found no module-level definitions at all"
    assert [name for name in definitions if name not in usmap.__all__] == []


def test_every_exported_name_resolves() -> None:
    """The forward direction, kept as the other half of the pair.

    On its own this proves very little - see the section note above - but the
    two together pin ``__all__`` to the module exactly.
    """
    assert [name for name in usmap.__all__ if not hasattr(usmap, name)] == []


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


# ---------------------------------------------------------------------------
# 11 - CS-419: an unresolvable enum MEMBER index is flagged, not dropped
#
# The same non-negotiable 7 half as section 7 above and the same
# ``_resolve``-returns-None root cause, but a DIFFERENT MECHANISM. CS-417 was a
# missing check; this is a check that DISCARDS without flagging - the member
# loop tested ``is not None`` and simply did not append, while the enum-name
# check three lines away in the same loop did log.
#
# That difference is why it needs its own control. A truncated enum renders as
# a shorter enum, and a shorter enum is a perfectly ordinary thing for the
# shipped file to contain, so the failure arrives wearing the costume of a
# success. The shipped file carries no out-of-bounds member index, so neither
# the landing oracle nor the rebuild audit can reach this path either.
# ---------------------------------------------------------------------------

#: The enum fixture, invented like every other name in this file. The member
#: names are ordered so that a positional drop is visible in the result tuple.
_SYNTH_ENUM = "ESynthEnum"
_OTHER_ENUM = "ESynthOther"
_MEMBER_ZERO = "Member0"
_MEMBER_ONE = "Member1"

#: The one-enum table, and the indices ``build_usmap_body`` writes for it.
#: Spelled as literals rather than computed with ``list.index``, so that the
#: anchor is an independent statement about the bytes and not a restatement of
#: the builder's own opinion of them.
_ENUM_NAMES = [_SYNTH_ENUM, _MEMBER_ZERO, _MEMBER_ONE]
_INDEX_OF_SYNTH_ENUM = 0
_INDEX_OF_MEMBER_ZERO = 1
_INDEX_OF_MEMBER_ONE = 2

#: The two-enum table, for the cases that must not sit at position 0. Its
#: indices differ from the table above because a name was inserted at 1.
_TWO_ENUM_NAMES = [_SYNTH_ENUM, _OTHER_ENUM, _MEMBER_ZERO, _MEMBER_ONE]
_PAIR_INDEX_OF_OTHER_ENUM = 1
_PAIR_INDEX_OF_MEMBER_ZERO = 2
_PAIR_INDEX_OF_MEMBER_ONE = 3

_BOTH_MEMBERS = [_MEMBER_ZERO, _MEMBER_ONE]
_ONE_ENUM = [(_SYNTH_ENUM, _BOTH_MEMBERS)]

#: Widths inside the enum section: the enum count (4), each enum's own name
#: index (4), its uint8 member count (1) and each member index (4).
_ENUM_COUNT_WIDTH = 4
_ENUM_NAME_WIDTH = 4
_MEMBER_COUNT_WIDTH = 1
_MEMBER_INDEX_WIDTH = 4


def _enum_body(names: list[str], enums: list[tuple[str, list[str]]]) -> bytes:
    """A body holding ``enums`` and no schemas.

    Built through ``build_usmap(shipped=True)`` rather than :func:`_shipped_body`
    for the reason the module docstring gives: the corpus module owns the
    measurement, and its enum encoding is the one the rebuild control grades
    against the game's own bytes.
    """
    return synthetic.build_usmap_body(names=names, enums=list(enums), schemas=[], shipped=True)


def _enum_name_offset(names: list[str], enums: list[tuple[str, list[str]]], position: int) -> int:
    """Byte offset of enum ``position``'s own uint32 name index.

    The name count, then every name, then the enum count, then each PRECEDING
    enum's fixed head and its member indices. Walking the preceding enums is
    what lets a fixture put the broken enum somewhere other than position 0.
    """
    at = 4 + sum(1 + len(text) for text in names) + _ENUM_COUNT_WIDTH
    for _name, members in enums[:position]:
        at += _ENUM_NAME_WIDTH + _MEMBER_COUNT_WIDTH + len(members) * _MEMBER_INDEX_WIDTH
    return at


def _enum_member_offset(
    names: list[str], enums: list[tuple[str, list[str]]], position: int, member: int
) -> int:
    """Byte offset of member ``member``'s uint32 index inside enum ``position``."""
    return (
        _enum_name_offset(names, enums, position)
        + _ENUM_NAME_WIDTH
        + _MEMBER_COUNT_WIDTH
        + member * _MEMBER_INDEX_WIDTH
    )


def _patched_enum_body(
    names: list[str],
    enums: list[tuple[str, list[str]]],
    patches: list[tuple[int, int]],
) -> bytes:
    """``enums`` as a body, with every ``(offset, anchor)`` made unresolvable.

    ``anchor`` is what that uint32 must hold BEFORE the overwrite, and it is
    asserted, for the reason :func:`_patched_body` gives: a patch that lands on
    the wrong offset leaves every test built on it green while testing nothing.

    Takes a LIST of sites because the interesting case for the aggregation key
    is two failures inside one enum, which a single-site helper cannot build.
    """
    body = bytearray(_enum_body(names, enums))
    for at, anchor in patches:
        (found,) = struct.unpack_from("<I", body, at)
        assert found == anchor, f"byte {at} holds {found}, not the expected anchor {anchor}"
        struct.pack_into("<I", body, at, _UNRESOLVABLE_INDEX)
    return bytes(body)


def _parse_enum_body(body: bytes) -> usmap.PropertyMap:
    """Frame a body in the builder's own outer framing and parse it."""
    return usmap.parse_usmap(_reframe(synthetic.build_usmap(names=[], enums=[], schemas=[]), body))


def _detail_for(parsed: usmap.PropertyMap, code: str, subject: str) -> str:
    """The detail line of the one warning with ``(code, subject)``.

    Returns the detail rather than asserting a literal sentence anywhere. A
    test that restated the module's prose would go red on a wording change and
    green on a wording LIE; comparing one parse's detail against another
    parse's pins the thing that actually matters - that the true sentence for a
    condition is still the sentence that condition produces.
    """
    matching = [w.detail for w in parsed.warnings if w.code == code and w.subject == subject]
    assert len(matching) == 1, f"expected exactly one {code}/{subject}, got {len(matching)}"
    return matching[0]


def test_a_truncated_enum_is_flagged_rather_than_passing_as_a_genuinely_short_one() -> None:
    """CS-419. The exact confusion the finder demonstrated, pinned both ways.

    One body declares ONE member. The other declares TWO and holds an index no
    three-name table can resolve in the second, so the second member is
    dropped. Both therefore yield the identical one-member enum, the identical
    name table and a fully consumed body - so whether the dropped member was
    FLAGGED is the entire difference between them, exactly as it was between
    CS-417's two schemas.

    Both directions are asserted. A test that only checked the warning fires
    would pass just as happily against an implementation that warned on every
    enum, the genuinely-short one included, and that distinguishes nothing.
    """
    genuine = _parse_enum_body(_enum_body(_ENUM_NAMES, [(_SYNTH_ENUM, [_MEMBER_ZERO])]))
    truncated = _parse_enum_body(
        _patched_enum_body(
            _ENUM_NAMES,
            _ONE_ENUM,
            [(_enum_member_offset(_ENUM_NAMES, _ONE_ENUM, 0, 1), _INDEX_OF_MEMBER_ONE)],
        )
    )

    # Everything a caller can read about the enum is identical ...
    assert genuine.enums == {_SYNTH_ENUM: (_MEMBER_ZERO,)}
    assert truncated.enums == genuine.enums
    assert truncated.names == genuine.names
    assert truncated.schemas == genuine.schemas
    assert truncated.body_consumed == truncated.container.compressed_size
    # ... so the warnings are the only place the difference can show up. The
    # genuinely-short enum is silent: the negative control that gives the next
    # assertion its meaning.
    assert genuine.warnings == ()
    # And the dropped member is flagged, naming its enum by POSITION and its
    # own site within that enum. Asserted as what IS there, not as an absence.
    assert [(warning.code, warning.subject) for warning in truncated.warnings] == [
        (usmap.WARN_UNRESOLVED_NAME, "enum-0-member")
    ]


def test_an_unresolvable_enum_member_keeps_the_enum_and_every_readable_member() -> None:
    """Flagged and SKIPPED, never fatal - the first half of non-negotiable 7.

    The FIRST member is the unreadable one here, where the test above breaks
    the last. A fix that only noticed a trailing member would be green there
    and red here, and the surviving member proves the drop is positional rather
    than the whole enum being discarded to report one bad index.
    """
    parsed = _parse_enum_body(
        _patched_enum_body(
            _ENUM_NAMES,
            _ONE_ENUM,
            [(_enum_member_offset(_ENUM_NAMES, _ONE_ENUM, 0, 0), _INDEX_OF_MEMBER_ZERO)],
        )
    )

    assert parsed.enums == {_SYNTH_ENUM: (_MEMBER_ONE,)}
    assert parsed.body_consumed == parsed.container.compressed_size
    assert [(warning.code, warning.subject) for warning in parsed.warnings] == [
        (usmap.WARN_UNRESOLVED_NAME, "enum-0-member")
    ]


@pytest.mark.parametrize(
    ("site", "member_position", "anchor"),
    [
        ("enum-name", None, _INDEX_OF_SYNTH_ENUM),
        ("member-0", 0, _INDEX_OF_MEMBER_ZERO),
        ("member-1", 1, _INDEX_OF_MEMBER_ONE),
    ],
)
def test_every_unresolvable_name_index_in_an_enum_raises_the_same_code(
    site: str, member_position: int | None, anchor: int
) -> None:
    """Parity across every name index the enum section carries.

    Before CS-419 the two member rows were the odd ones out: they mapped an
    unresolvable index to None and said nothing at all, while the first row -
    the same ``_resolve`` call, three lines away, inside the same loop - logged.
    Parametrized rather than written three times so that flagging one site and
    forgetting another goes red, which is the control section 7's equivalent
    test provides for schemas and which this section did not have.
    """
    at = (
        _enum_name_offset(_ENUM_NAMES, _ONE_ENUM, 0)
        if member_position is None
        else _enum_member_offset(_ENUM_NAMES, _ONE_ENUM, 0, member_position)
    )

    parsed = _parse_enum_body(_patched_enum_body(_ENUM_NAMES, _ONE_ENUM, [(at, anchor)]))

    codes = {warning.code for warning in parsed.warnings}
    assert codes == {usmap.WARN_UNRESOLVED_NAME}, f"{site} at byte {at}"
    assert parsed.body_consumed == parsed.container.compressed_size, "the parse did not complete"


def test_a_failed_member_does_not_swallow_the_enum_skipped_warning() -> None:
    """The aggregation key must not merge two different conditions.

    ``_WarningLog`` aggregates by ``(code, subject)`` and KEEPS THE FIRST
    DETAIL SEEN, and the member loop runs before the enum-name check. Sharing
    one subject therefore let the member's detail win and buried the enum-name
    warning behind a count of 2 - and the surviving sentence said the enum was
    "shorter than the file declares" while the enum was in fact ABSENT. A true
    warning replaced by a false one is the same "never silently wrong" half of
    non-negotiable 7 that CS-419 exists to enforce.

    No literal sentence is asserted here. Each condition's detail is compared
    against the detail THAT SAME CONDITION produces when it happens alone, so
    the test pins the behaviour and cannot be satisfied by rewording, nor go
    red because of it.
    """
    name_at = (_enum_name_offset(_ENUM_NAMES, _ONE_ENUM, 0), _INDEX_OF_SYNTH_ENUM)
    member_at = (_enum_member_offset(_ENUM_NAMES, _ONE_ENUM, 0, 1), _INDEX_OF_MEMBER_ONE)

    name_only = _parse_enum_body(_patched_enum_body(_ENUM_NAMES, _ONE_ENUM, [name_at]))
    member_only = _parse_enum_body(_patched_enum_body(_ENUM_NAMES, _ONE_ENUM, [member_at]))
    both = _parse_enum_body(_patched_enum_body(_ENUM_NAMES, _ONE_ENUM, [name_at, member_at]))

    # The enum really is gone in both cases that break its name, which is what
    # makes a "shorter than declared" sentence about it false.
    assert name_only.enums == {}
    assert both.enums == {}

    # Two conditions, two warnings, neither one's detail displaced by the other.
    assert [(w.code, w.subject) for w in both.warnings] == [
        (usmap.WARN_UNRESOLVED_NAME, "enum-0-member"),
        (usmap.WARN_UNRESOLVED_NAME, "enum-0"),
    ]
    assert _detail_for(both, usmap.WARN_UNRESOLVED_NAME, "enum-0") == _detail_for(
        name_only, usmap.WARN_UNRESOLVED_NAME, "enum-0"
    )
    assert _detail_for(both, usmap.WARN_UNRESOLVED_NAME, "enum-0-member") == _detail_for(
        member_only, usmap.WARN_UNRESOLVED_NAME, "enum-0-member"
    )
    # And each is counted once, not merged into a single entry counted twice.
    assert [w.count for w in both.warnings] == [1, 1]


def test_the_flagged_enum_is_named_by_its_own_position_not_the_first() -> None:
    """The subject tracks the enum, which one enum at position 0 cannot show.

    Every other fixture in this section builds a single enum, so a mutant that
    hardcoded the subject to the literal ``enum-0`` produced byte-identical
    suite results. The broken enum here is the SECOND one, and the healthy
    first enum is asserted intact so the warning cannot be read as covering it.
    """
    enums = [(_SYNTH_ENUM, [_MEMBER_ZERO]), (_OTHER_ENUM, _BOTH_MEMBERS)]
    at = _enum_member_offset(_TWO_ENUM_NAMES, enums, 1, 1)

    parsed = _parse_enum_body(
        _patched_enum_body(_TWO_ENUM_NAMES, enums, [(at, _PAIR_INDEX_OF_MEMBER_ONE)])
    )

    assert parsed.enums == {_SYNTH_ENUM: (_MEMBER_ZERO,), _OTHER_ENUM: (_MEMBER_ZERO,)}
    assert [(w.code, w.subject) for w in parsed.warnings] == [
        (usmap.WARN_UNRESOLVED_NAME, "enum-1-member")
    ]


def test_the_flagged_enum_name_is_flagged_at_its_own_position() -> None:
    """CS-437. The positional control the enum-NAME subject lacked.

    ``enum-N`` is the enum section's counterpart to the bare ``schema-N``: the
    subject for the condition that decides whether the enum survives at all.
    The two-enum fixture above breaks a MEMBER, and every fixture here that
    breaks an enum's own NAME holds one enum at position 0, where a literal and
    an interpolation are indistinguishable.

    The broken enum is the SECOND one. A subject built from the literal 0 rather
    than from ``position`` reports the loss against the first enum, which is
    intact here and asserted so.
    """
    enums = [(_SYNTH_ENUM, [_MEMBER_ZERO]), (_OTHER_ENUM, _BOTH_MEMBERS)]
    at = _enum_name_offset(_TWO_ENUM_NAMES, enums, 1)

    parsed = _parse_enum_body(
        _patched_enum_body(_TWO_ENUM_NAMES, enums, [(at, _PAIR_INDEX_OF_OTHER_ENUM)])
    )

    # The healthy first enum survives whole, so the warning cannot be read as
    # covering it, and the second enum is gone rather than merely short.
    assert parsed.enums == {_SYNTH_ENUM: (_MEMBER_ZERO,)}
    assert parsed.body_consumed == parsed.container.compressed_size
    assert [(w.code, w.subject) for w in parsed.warnings] == [
        (usmap.WARN_UNRESOLVED_NAME, "enum-1")
    ]


def test_a_one_member_enum_whose_only_member_is_unresolvable_is_flagged() -> None:
    """The single-member case, which is the CS-419 defect at its smallest.

    Both of the other member fixtures declare two members, so a mutant guarding
    the flag with ``member_count > 1`` restored the entire defect undetected:
    an enum arriving EMPTY, fully consumed, with no warning at all. An empty
    enum is not something a caller can distinguish from a genuinely empty one
    any more than a short one was.
    """
    enums = [(_SYNTH_ENUM, [_MEMBER_ZERO])]
    at = _enum_member_offset(_ENUM_NAMES, enums, 0, 0)

    parsed = _parse_enum_body(_patched_enum_body(_ENUM_NAMES, enums, [(at, _INDEX_OF_MEMBER_ZERO)]))

    assert parsed.enums == {_SYNTH_ENUM: ()}
    assert parsed.body_consumed == parsed.container.compressed_size
    assert [(w.code, w.subject) for w in parsed.warnings] == [
        (usmap.WARN_UNRESOLVED_NAME, "enum-0-member")
    ]


def test_a_repeated_enum_name_is_flagged_the_way_a_repeated_schema_name_is() -> None:
    """The sibling that survived inside the function CS-419 edited.

    ``_read_enums`` ended with a bare ``enums[enum_name] = ...``, so two enums
    sharing a name collapsed into one with NO warning - while ``_read_schemas``
    at the same commit flagged the identical loss. That is the same
    one-branch-logs-one-does-not asymmetry that produced CS-419, one section
    away, and the shape of the fix is taken from the schema side deliberately.

    The surviving definition is asserted as the LATER one, so the warning's
    account of what happened is checked rather than just its existence.
    """
    enums = [(_SYNTH_ENUM, [_MEMBER_ZERO]), (_SYNTH_ENUM, [_MEMBER_ONE])]

    parsed = _parse_enum_body(_enum_body(_ENUM_NAMES, enums))

    assert parsed.enums == {_SYNTH_ENUM: (_MEMBER_ONE,)}
    assert parsed.body_consumed == parsed.container.compressed_size
    assert [(w.code, w.subject) for w in parsed.warnings] == [(usmap.WARN_DUPLICATE_ENUM, "enum-1")]


def test_a_healthy_enum_section_stays_silent() -> None:
    """The negative control for every warning this section added.

    Two distinctly named enums with resolvable members must produce NOTHING.
    Without this, a fix that flagged unconditionally would satisfy every
    assertion above.
    """
    enums = [(_SYNTH_ENUM, [_MEMBER_ZERO]), (_OTHER_ENUM, _BOTH_MEMBERS)]

    parsed = _parse_enum_body(_enum_body(_TWO_ENUM_NAMES, enums))

    assert parsed.enums == {_SYNTH_ENUM: (_MEMBER_ZERO,), _OTHER_ENUM: tuple(_BOTH_MEMBERS)}
    assert parsed.warnings == ()


# ---------------------------------------------------------------------------
# 12 - CS-424: the parsed mapping's reprs render structure, not the name table
#
# SEVERITY, STATED EXACTLY. This is NOT a non-negotiable 12 breach. The strings
# withheld here are PUBLISHER-OWNED GAME ASSET names, not personal data, and
# calling it a privacy defect would overstate it - which this project treats as
# its own defect. It is diagnostic noise and an asset echo: the default
# dataclass repr renders the whole name table, which on the pinned build is
# five figures of strings in front of whatever a reader was actually looking
# for. It was filed off a mutant run whose assertion opened with the first
# entries of that table; those entries are NOT reproduced here, because this
# file is tracked and the module it tests says the mapping is never copied or
# committed (non-negotiable 2).
#
# The discipline is not new here. clockspeed/save/objects.py already applies
# exactly it to ObjectRecord and ObjectTable, for the reason that generalises
# to any of them: a test runner and most loggers repr an object BEFORE a human
# chooses what to print, so the safe rendering has to be the default one.
#
# TWO ORACLES, BECAUSE ONE OF THEM CANNOT RUN EVERYWHERE.
#   presence  - no FIXTURE name appears in the rendering. Runs anywhere. Sound
#               only because the fixture names below are distinctive; it would
#               be worthless against the real table, whose short entries
#               collide with this module's own field labels.
#   quoting   - a withholding repr emits NO string literal at all, so the
#               rendering must contain no quote character. Independent of what
#               the names ARE, which is what lets it run against the real
#               install, and it does not restate the repr's format, which is
#               what stops it going red the day a field is added.
# ---------------------------------------------------------------------------

#: A body exercising all three name-bearing collections at once: the name
#: table, an enum with members, and a schema with a super type and properties.
#: Every name is invented, like every other name in this file, and each is
#: distinctive enough not to collide with a field label in any repr below.
_REPR_NAMES = ["Alpha", "Beta", "ESynthEnum", "Member0", "Member1", "SynthSchema", "SynthBase"]

#: Quote characters a Python repr would use to open a string literal.
_QUOTE_CHARACTERS = "'\""


def _parsed_for_repr() -> usmap.PropertyMap:
    """Parse a mapping whose every name-bearing collection is populated."""
    framing = synthetic.build_usmap(names=[], enums=[], schemas=[])
    body = _shipped_body(
        names=_REPR_NAMES,
        enums=[(_SYNTH_ENUM, [_MEMBER_ZERO, _MEMBER_ONE])],
        schemas=[("SynthSchema", "SynthBase", [("Alpha", _TYPE_INT), ("Beta", _TYPE_BOOL)])],
    )
    parsed = usmap.parse_usmap(_reframe(framing, body))
    # FIXTURE LIVENESS. Every presence assertion below iterates this table, so
    # an empty one turns all of them into zero-iteration loops that pass while
    # testing nothing - CONVENTIONS.md section 7.2, "a mutation that fails to
    # apply looks GREEN". Asserted once here rather than in each test.
    assert len(parsed.names) == len(_REPR_NAMES), "the fixture lost its name table"
    assert parsed.schemas, "the fixture lost its schemas"
    assert parsed.enums, "the fixture lost its enums"
    return parsed


def _assert_withholds(rendering: str, names: tuple[str, ...], what: str) -> None:
    """Assert no FIXTURE name appears in ``rendering``.

    The names are the invented ones this file builds its bodies from, NOT names
    out of the install - the distinction matters because this module uses
    "shipped" everywhere else to mean the latter, and the real table cannot be
    checked this way at all (see :func:`test_the_real_usmap_repr_quotes_nothing`).

    Iterates the parse's OWN name table rather than a restated literal, so a
    fixture that grows a name cannot outrun the assertion.

    THE EMPTY STRING IS SKIPPED, and that is not a hole in the sweep. ``in`` is
    vacuously true for it against every possible rendering, so including it can
    only produce a hit on a provably clean string - and an empty name has
    nothing in it to leak. CS-435 is what put one in a name table: an
    undecodable name is published as the empty string so that every later index
    stays aligned, and the warning beside it is what says so.
    """
    for name in names:
        if not name:
            continue
        assert name not in rendering, f"{what} renders the fixture name {name!r}"


def _assert_quotes_nothing(rendering: str, what: str) -> None:
    """Assert ``rendering`` opens no string literal.

    A repr that withholds every string has no reason to emit a quote, so this
    holds whatever the strings happen to BE. That independence is the whole
    point: it is the only one of the two oracles that can be pointed at the
    install.
    """
    found = [character for character in rendering if character in _QUOTE_CHARACTERS]
    assert not found, f"{what} emitted {len(found)} quote characters, so it rendered a string"


def test_the_property_map_repr_renders_structure_rather_than_its_name_table() -> None:
    """CS-424. The acceptance: counts and structure, no name table.

    Both halves are asserted. Presence-only on its own would be satisfied by a
    repr that rendered nothing at all, so the STRUCTURE is asserted as what IS
    there - a withholding repr still has to be worth reading, and every field
    it is supposed to carry is named so that one quietly disappearing goes red.
    """
    parsed = _parsed_for_repr()

    rendered = repr(parsed)

    _assert_withholds(rendered, parsed.names, "PropertyMap")
    _assert_quotes_nothing(rendered, "PropertyMap")
    assert type(parsed).__name__ in rendered
    assert f"names={len(parsed.names)}" in rendered
    assert f"enums={len(parsed.enums)}" in rendered
    assert f"schemas={len(parsed.schemas)}" in rendered
    assert f"warnings={len(parsed.warnings)}" in rendered
    assert f"body_consumed={parsed.body_consumed}" in rendered
    # The framing is structure too, and it is the part a reader wants first.
    # Named explicitly because a repr that silently stopped carrying it still
    # satisfied every other assertion here.
    assert "container=" in rendered
    assert repr(parsed.container) in rendered


def test_a_schema_and_its_property_entries_render_structure_rather_than_names() -> None:
    """The two SIBLINGS of the same defect, found by grepping this module.

    ``PropertyMap`` was the one filed, but ``Schema`` and ``PropertyEntry`` are
    the same construct - a frozen dataclass carrying name strings under the
    default repr - and a caller reaches both of them straight off the mapping.
    Fixing only the one named would leave the identical echo one attribute
    away, which is exactly how CS-419 came to exist.

    The CONTAINER renderings are asserted too, because a tuple reprs its
    elements: a fix applied to the element type is what makes the collection
    safe, and asserting only the element would miss a regression that
    reintroduced a name at the collection level.
    """
    parsed = _parsed_for_repr()
    schema = parsed.schemas["SynthSchema"]
    entry = schema.properties[0]

    for what, rendering in (
        ("Schema", repr(schema)),
        ("a tuple of Schema", repr(tuple(parsed.schemas.values()))),
        ("PropertyEntry", repr(entry)),
        ("Schema.properties", repr(schema.properties)),
    ):
        _assert_withholds(rendering, parsed.names, what)
        _assert_quotes_nothing(rendering, what)

    assert f"properties={len(schema.properties)}" in repr(schema)
    # Whether a super type resolved is the one bit of structure Schema has
    # beyond its count, and CS-417 turned it into load-bearing information.
    assert "super=" in repr(schema)
    assert f"slot={entry.slot}" in repr(entry)
    assert f"array_size={entry.array_size}" in repr(entry)
    assert f"type_id={entry.type_id}" in repr(entry)


def test_every_warning_this_module_can_raise_carries_a_structural_subject() -> None:
    """``_WarningLog.add``'s stated invariant, measured across every code.

    NARROWED DELIBERATELY FROM WHAT THIS TEST FIRST CLAIMED. It previously said
    ``UsmapWarning`` was safe "by construction" and that it guarded "the whole
    returned surface". There IS no construction - no type, no gate, nothing
    stops a future edit interpolating a name - and a fixture that reaches one
    warning site cannot speak for the others. So the claim is now exactly the
    measurement: every code this module defines is provoked here, and every
    subject and detail is checked against the fixture names that produced it.

    The liveness assertion is what keeps that honest. Without it a refactor
    that stopped raising a code would silently shrink the test's reach.
    """
    observed: dict[str, list[usmap.UsmapWarning]] = {}
    fixture_names: set[str] = set()

    def collect(mapping: usmap.PropertyMap) -> None:
        fixture_names.update(mapping.names)
        for warning in mapping.warnings:
            observed.setdefault(warning.code, []).append(warning)

    # An unresolvable enum name, an unresolvable enum member, and a repeat.
    collect(
        _parse_enum_body(
            _patched_enum_body(
                _ENUM_NAMES,
                _ONE_ENUM,
                [
                    (_enum_name_offset(_ENUM_NAMES, _ONE_ENUM, 0), _INDEX_OF_SYNTH_ENUM),
                    (_enum_member_offset(_ENUM_NAMES, _ONE_ENUM, 0, 1), _INDEX_OF_MEMBER_ONE),
                ],
            )
        )
    )
    collect(
        _parse_enum_body(
            _enum_body(_ENUM_NAMES, [(_SYNTH_ENUM, [_MEMBER_ZERO]), (_SYNTH_ENUM, [_MEMBER_ONE])])
        )
    )
    # All three of a schema's name indices, and a repeated schema name.
    schema_names = ["Alpha", "SynthSchema"]
    for delta, anchor in (
        (_SCHEMA_NAME_DELTA, _INDEX_OF_SYNTH_SCHEMA),
        (0, _ALL_BITS_SET),
        (_PROPERTY_NAME_DELTA, _INDEX_OF_ALPHA),
    ):
        at = _super_index_offset(schema_names) + delta
        collect(_parse_enum_body(_patched_body(schema_names, at, _UNRESOLVABLE_INDEX, anchor)))
    collect(
        _parse_enum_body(
            _shipped_body(
                names=schema_names,
                enums=[],
                schemas=[
                    ("SynthSchema", None, [("Alpha", _TYPE_INT)]),
                    ("SynthSchema", None, [("Alpha", _TYPE_INT)]),
                ],
            )
        )
    )
    # An unknown property type, and a trailing section after the schemas.
    collect(
        _parse_enum_body(
            _shipped_body(
                names=["Only", "SynthSchema"],
                enums=[],
                schemas=[("SynthSchema", None, [("Only", _UNKNOWN_TYPE)])],
            )
        )
    )
    collect(_parse_enum_body(_shipped_body(names=["Alpha"], enums=[], schemas=[]) + b"CEXT"))
    # A name whose bytes are not valid UTF-8 (CS-435). Added here rather than
    # left to section 14 because the liveness assertion below demands every
    # WARN_* the module defines be reached by THIS test.
    collect(
        _parse_schema_body(
            _with_undecodable_name(
                _shipped_body(
                    names=_UNDECODABLE_FIRST,
                    enums=[],
                    schemas=[("SynthSchema", None, [("Alpha", _TYPE_INT)])],
                ),
                _UNDECODABLE_FIRST,
                0,
            )
        )
    )
    # A schema section cut short mid-entry, which desynchronises the walk.
    short = _shipped_body(
        names=["Alpha", "First", "Second"],
        enums=[],
        schemas=[
            ("First", None, [("Alpha", _TYPE_INT)]),
            ("Second", None, [("Alpha", _TYPE_INT)]),
        ],
    )
    collect(_parse_enum_body(short[: len(short) - 6]))
    # A file version nobody here has read.
    collect(
        usmap.parse_usmap(
            synthetic.build_usmap(names=[], enums=[], schemas=[], version=_VERSION_UNKNOWN)
        )
    )

    # LIVENESS: every WARN_* the module defines was actually provoked. Without
    # this the assertions below could pass by reaching nothing.
    expected_codes = {
        value
        for name, value in vars(usmap).items()
        if name.startswith("WARN_") and isinstance(value, str)
    }
    assert set(observed) == expected_codes, f"unreached: {sorted(expected_codes - set(observed))}"

    # SECOND LIVENESS GUARD, for the same reason _parsed_for_repr carries one:
    # the sweep below iterates these names, so an empty set would turn it into
    # a loop over nothing that passes while checking nothing.
    assert _SYNTH_ENUM in fixture_names
    assert "SynthSchema" in fixture_names

    # And no subject or detail carries a name out of the body that produced it.
    for code, warnings in observed.items():
        for warning in warnings:
            _assert_withholds(warning.subject, tuple(fixture_names), f"{code} subject")
            _assert_withholds(warning.detail, tuple(fixture_names), f"{code} detail")


def test_the_real_usmap_repr_quotes_nothing() -> None:
    """The withholding claim, run against the INSTALL rather than a fixture.

    Skipped with a reason where there is no game, like every other test in this
    file that opens the shipped file. The oracle is quoting rather than
    presence because presence cannot work here: the real table holds short
    entries that are substrings of this module's own field labels, so a
    presence sweep reports hits on a provably clean rendering. It is also not a
    restatement of the repr's format, so adding a field does not break it.

    Asserts SHAPES ONLY and prints nothing (non-negotiable 2).
    """
    parsed = usmap.cached_usmap()
    if parsed is None:
        pytest.skip("no game install resolved on this machine, or it carries no usmap")

    assert parsed.names, "the install parsed to an empty name table"
    richest = max(parsed.schemas.values(), key=lambda schema: len(schema.properties))
    assert richest.properties, "no schema in the install carried a property"

    _assert_quotes_nothing(repr(parsed), "the real PropertyMap")
    _assert_quotes_nothing(repr(parsed.container), "the real UsmapContainer")
    _assert_quotes_nothing(repr(richest), "the real Schema")
    _assert_quotes_nothing(repr(richest.properties), "the real Schema.properties")
    _assert_quotes_nothing(repr(richest.properties[0]), "the real PropertyEntry")


# ---------------------------------------------------------------------------
# 13 - CS-431: the schema section's three failures get three SUBJECTS
#
# THE SAME AGGREGATION-KEY COLLISION CS-419 CLOSED ONE SECTION OVER, in code
# that predates it. ``_read_schema`` logged all three of its unresolvable-index
# conditions under one ``(WARN_UNRESOLVED_NAME, "schema-N")`` key, and
# ``_WarningLog`` keeps the FIRST detail it was given - so a schema failing two
# ways surfaced ONE warning carrying the sentence of whichever condition ran
# first, with the other reduced to a count nobody can attribute.
#
# THAT IS NOT AN UNDER-REPORT, IT IS A FALSE REPORT, and the measured case is
# the sharp one: with the schema name AND the super index unresolvable the
# schema is ABSENT from the mapping, and the one surviving sentence said its
# super type was not resolved - a statement about the super type of a schema
# that is not there. A true sentence replaced by a false one is the "never
# silently wrong" half of non-negotiable 7, and it is the exact regression
# CS-419's first round shipped and an adversary caught.
#
# THE SUBJECTS FOLLOW THE ENUM SECTION'S SHAPE DELIBERATELY: the bare
# ``schema-N`` stays with the schema's OWN name - the condition that decides
# whether the schema survives at all - and each sub-site qualifies it, exactly
# as ``enum-N`` and ``enum-N-member`` do.
# ---------------------------------------------------------------------------

#: Bytes a schema entry spends before its first property: name index, super
#: index, property count, serializable count.
_SCHEMA_FIXED_BYTES = 12

#: Bytes one property entry spends for a type that carries no payload: slot,
#: array size, name index, type byte.
_SCHEMA_PROPERTY_BYTES = 8

_OTHER_SCHEMA = "OtherSchema"

#: Name tables for the one- and two-schema fixtures below.
_SCHEMA_NAMES = ["Alpha", "SynthSchema"]
_TWO_SCHEMA_NAMES = ["Alpha", "SynthSchema", _OTHER_SCHEMA]

#: The schema lists, in ``_shipped_body``'s own argument shape.
_ONE_SCHEMA: list[tuple[str, str | None, list[tuple[str, int]]]] = [
    ("SynthSchema", None, [("Alpha", _TYPE_INT)])
]
_TWO_SCHEMAS: list[tuple[str, str | None, list[tuple[str, int]]]] = [
    ("SynthSchema", None, [("Alpha", _TYPE_INT)]),
    (_OTHER_SCHEMA, None, [("Alpha", _TYPE_INT)]),
]

#: Three schemas whose FIRST and THIRD share a name, so the duplicate is
#: detected at position 2 rather than at 0 or 1. The repeat carries a different
#: property type from the original, which is how the surviving definition is
#: identified without restating the loader's opinion of which one won.
_DUPLICATE_SCHEMAS: list[tuple[str, str | None, list[tuple[str, int]]]] = [
    ("SynthSchema", None, [("Alpha", _TYPE_INT)]),
    (_OTHER_SCHEMA, None, [("Alpha", _TYPE_INT)]),
    ("SynthSchema", None, [("Alpha", _TYPE_BOOL)]),
]

#: What ``_shipped_body`` writes at the second schema's own name index.
_INDEX_OF_OTHER_SCHEMA = 2

#: Three conditions must produce three DIFFERENT sentences. Sharing one would
#: be the collision this section removes wearing three subjects.
_TRIPLE_DISTINCT_DETAILS = 3


def _schema_super_offset(
    names: list[str],
    schemas: list[tuple[str, str | None, list[tuple[str, int]]]],
    position: int,
) -> int:
    """Byte offset of one schema's super index inside a ``_shipped_body``.

    The generalisation of :func:`_super_index_offset`, which holds only for a
    body with one schema and no enums. Every earlier schema's encoded length is
    walked rather than assumed, so a second schema can be reached. Both are
    kept: the older one is the anchor the CS-417 tests are already written
    against, and it is asserted equal to this one at position 0 below.
    """
    at = 4 + sum(1 + len(text) for text in names) + 4 + 4
    for earlier in schemas[:position]:
        at += _SCHEMA_FIXED_BYTES + _SCHEMA_PROPERTY_BYTES * len(earlier[2])
    return at + 4


def _patched_schema_body(
    names: list[str],
    schemas: list[tuple[str, str | None, list[tuple[str, int]]]],
    patches: list[tuple[int, int]],
) -> bytes:
    """``schemas`` as a body, with every ``(offset, anchor)`` made unresolvable.

    ``anchor`` is what that uint32 must hold BEFORE the overwrite, and it is
    asserted, for the reason :func:`_patched_body` gives: a patch that lands on
    the wrong offset leaves every test built on it green while testing nothing.

    Takes a LIST of sites for the reason :func:`_patched_enum_body` does - the
    interesting case for the aggregation key is two failures inside ONE schema,
    which the single-site helper cannot build - and it exists alongside that
    helper rather than replacing it, exactly as the enum section's does.
    """
    body = bytearray(_shipped_body(names=names, enums=[], schemas=schemas))
    for at, anchor in patches:
        (found,) = struct.unpack_from("<I", body, at)
        assert found == anchor, f"byte {at} holds {found}, not the expected anchor {anchor}"
        struct.pack_into("<I", body, at, _UNRESOLVABLE_INDEX)
    return bytes(body)


def _parse_schema_body(body: bytes) -> usmap.PropertyMap:
    """Frame a schema-section body in the builder's outer framing and parse it."""
    return usmap.parse_usmap(_reframe(synthetic.build_usmap(names=[], enums=[], schemas=[]), body))


def test_the_two_schema_offset_walks_agree_where_both_are_defined() -> None:
    """The new offset helper against the one CS-417's tests are written on.

    They must agree at position 0 or one of the two sections is patching bytes
    the other is not, and every anchor assertion downstream would still pass
    because each helper is self-consistent.
    """
    assert _schema_super_offset(_SCHEMA_NAMES, _ONE_SCHEMA, 0) == _super_index_offset(_SCHEMA_NAMES)


def test_a_failed_super_index_does_not_swallow_the_schema_skipped_warning() -> None:
    """CS-431 acceptance. Two conditions in one schema, two warnings, both true.

    ``_WarningLog`` aggregates by ``(code, subject)`` and KEEPS THE FIRST DETAIL
    SEEN, and the super-index check runs before the schema-name check. Sharing
    one subject therefore let the super index's detail win and buried the
    schema-skipped warning behind a count of 2 - and the surviving sentence
    described the super type of a schema that was in fact ABSENT.

    No literal sentence is asserted. Each condition's detail is compared against
    the detail THAT SAME CONDITION produces when it happens alone, so the test
    pins the behaviour and cannot be satisfied by rewording, nor go red because
    of it.
    """
    super_at = (_schema_super_offset(_SCHEMA_NAMES, _ONE_SCHEMA, 0), _ALL_BITS_SET)
    name_at = (
        _schema_super_offset(_SCHEMA_NAMES, _ONE_SCHEMA, 0) + _SCHEMA_NAME_DELTA,
        _INDEX_OF_SYNTH_SCHEMA,
    )

    super_only = _parse_schema_body(_patched_schema_body(_SCHEMA_NAMES, _ONE_SCHEMA, [super_at]))
    name_only = _parse_schema_body(_patched_schema_body(_SCHEMA_NAMES, _ONE_SCHEMA, [name_at]))
    both = _parse_schema_body(_patched_schema_body(_SCHEMA_NAMES, _ONE_SCHEMA, [name_at, super_at]))

    # The schema really is gone in both cases that break its name, which is what
    # makes a sentence about ITS super type false.
    assert name_only.schemas == {}
    assert both.schemas == {}
    # The super-only case keeps the schema, so the two conditions are genuinely
    # different losses rather than two names for one.
    assert sorted(super_only.schemas) == ["SynthSchema"]

    # Two conditions, two warnings, neither one's detail displaced by the other.
    assert [(w.code, w.subject) for w in both.warnings] == [
        (usmap.WARN_UNRESOLVED_NAME, "schema-0-super"),
        (usmap.WARN_UNRESOLVED_NAME, "schema-0"),
    ]
    assert _detail_for(both, usmap.WARN_UNRESOLVED_NAME, "schema-0") == _detail_for(
        name_only, usmap.WARN_UNRESOLVED_NAME, "schema-0"
    )
    assert _detail_for(both, usmap.WARN_UNRESOLVED_NAME, "schema-0-super") == _detail_for(
        super_only, usmap.WARN_UNRESOLVED_NAME, "schema-0-super"
    )
    # And each is counted once, not merged into a single entry counted twice.
    assert [w.count for w in both.warnings] == [1, 1]


def test_a_failed_property_name_does_not_swallow_the_schema_skipped_warning() -> None:
    """The sibling condition sharing the same key, found by the same mechanism.

    The property-name check also logged under the bare ``schema-N``, so a schema
    whose name AND one property name were unresolvable surfaced only "the
    property was skipped" - again while the whole schema was absent, and again
    with the true sentence displaced rather than merely missing. Fixing one of
    the two sub-sites and leaving the other is what this test refuses.
    """
    property_at = (
        _schema_super_offset(_SCHEMA_NAMES, _ONE_SCHEMA, 0) + _PROPERTY_NAME_DELTA,
        _INDEX_OF_ALPHA,
    )
    name_at = (
        _schema_super_offset(_SCHEMA_NAMES, _ONE_SCHEMA, 0) + _SCHEMA_NAME_DELTA,
        _INDEX_OF_SYNTH_SCHEMA,
    )

    property_only = _parse_schema_body(
        _patched_schema_body(_SCHEMA_NAMES, _ONE_SCHEMA, [property_at])
    )
    name_only = _parse_schema_body(_patched_schema_body(_SCHEMA_NAMES, _ONE_SCHEMA, [name_at]))
    both = _parse_schema_body(
        _patched_schema_body(_SCHEMA_NAMES, _ONE_SCHEMA, [name_at, property_at])
    )

    assert both.schemas == {}
    assert sorted(property_only.schemas) == ["SynthSchema"]

    assert [(w.code, w.subject) for w in both.warnings] == [
        (usmap.WARN_UNRESOLVED_NAME, "schema-0-property"),
        (usmap.WARN_UNRESOLVED_NAME, "schema-0"),
    ]
    assert _detail_for(both, usmap.WARN_UNRESOLVED_NAME, "schema-0") == _detail_for(
        name_only, usmap.WARN_UNRESOLVED_NAME, "schema-0"
    )
    assert _detail_for(both, usmap.WARN_UNRESOLVED_NAME, "schema-0-property") == _detail_for(
        property_only, usmap.WARN_UNRESOLVED_NAME, "schema-0-property"
    )
    assert [w.count for w in both.warnings] == [1, 1]


def test_all_three_schema_failures_at_once_produce_three_distinct_subjects() -> None:
    """Every name index a schema carries, broken together. Nothing may be lost.

    The two tests above each pin one pair, and a fix that gave the super site
    its own subject while leaving the property site on the bare one would pass
    the first. This is the whole-entry control: three conditions, three
    subjects, three counts of one - and the ORDER is asserted too, because the
    schema's own name is decided last and its warning is therefore the last one
    logged.
    """
    base = _schema_super_offset(_SCHEMA_NAMES, _ONE_SCHEMA, 0)
    patches = [
        (base + _SCHEMA_NAME_DELTA, _INDEX_OF_SYNTH_SCHEMA),
        (base, _ALL_BITS_SET),
        (base + _PROPERTY_NAME_DELTA, _INDEX_OF_ALPHA),
    ]

    parsed = _parse_schema_body(_patched_schema_body(_SCHEMA_NAMES, _ONE_SCHEMA, patches))

    assert parsed.schemas == {}
    assert [(w.code, w.subject) for w in parsed.warnings] == [
        (usmap.WARN_UNRESOLVED_NAME, "schema-0-super"),
        (usmap.WARN_UNRESOLVED_NAME, "schema-0-property"),
        (usmap.WARN_UNRESOLVED_NAME, "schema-0"),
    ]
    assert [w.count for w in parsed.warnings] == [1, 1, 1]
    assert len({w.detail for w in parsed.warnings}) == _TRIPLE_DISTINCT_DETAILS


def test_the_flagged_schema_is_named_by_its_own_position_not_the_first() -> None:
    """The subject tracks the schema, which one schema at position 0 cannot show.

    Every other fixture in this file builds a single schema, so a mutant that
    hardcoded the subject to the literal ``schema-0`` produced byte-identical
    suite results - the same gap CS-419 found and closed on the enum side. The
    broken schema here is the SECOND one, and the healthy first schema is
    asserted intact so the warning cannot be read as covering it.
    """
    at = _schema_super_offset(_TWO_SCHEMA_NAMES, _TWO_SCHEMAS, 1)

    parsed = _parse_schema_body(
        _patched_schema_body(_TWO_SCHEMA_NAMES, _TWO_SCHEMAS, [(at, _ALL_BITS_SET)])
    )

    assert sorted(parsed.schemas) == [_OTHER_SCHEMA, "SynthSchema"]
    assert [(w.code, w.subject) for w in parsed.warnings] == [
        (usmap.WARN_UNRESOLVED_NAME, "schema-1-super")
    ]


def test_the_flagged_property_is_named_by_its_own_schemas_position() -> None:
    """The third positional control, and the one CS-431 wrote the other two of.

    ``schema-N-super`` and the bare ``schema-N`` each got a two-schema control
    above, on the stated reasoning that a single schema at position 0 cannot
    tell ``position`` from the literal 0. ``schema-N-property`` is built by the
    same interpolation and was left without one, so replacing it with the
    literal ``schema-0-property`` changed no test result while attributing a
    lost property to the WRONG SCHEMA - a report the operator cannot act on and
    cannot detect, which is the failure mode this whole section exists for.

    The break is on the SECOND schema's property. Both schemas are asserted to
    survive, and the first one's property is asserted intact, so the warning
    cannot be read as covering it.
    """
    at = _schema_super_offset(_TWO_SCHEMA_NAMES, _TWO_SCHEMAS, 1) + _PROPERTY_NAME_DELTA

    parsed = _parse_schema_body(
        _patched_schema_body(_TWO_SCHEMA_NAMES, _TWO_SCHEMAS, [(at, _INDEX_OF_ALPHA)])
    )

    # Both schemas survive - only a property was lost - so the subject is the
    # only thing in the result that says WHICH schema lost it.
    assert sorted(parsed.schemas) == [_OTHER_SCHEMA, "SynthSchema"]
    assert [entry.name for entry in parsed.schemas["SynthSchema"].properties] == ["Alpha"]
    assert parsed.schemas[_OTHER_SCHEMA].properties == ()
    assert [(w.code, w.subject) for w in parsed.warnings] == [
        (usmap.WARN_UNRESOLVED_NAME, "schema-1-property")
    ]


def test_the_second_schemas_own_name_is_flagged_at_its_own_position() -> None:
    """The same positional claim for the subject that keeps the bare token.

    ``schema-N`` is the one subject CS-431 does NOT qualify, so it needs its own
    positional control: a fix that qualified the two sub-sites and left the bare
    subject hardcoded would be caught here and nowhere else.
    """
    at = _schema_super_offset(_TWO_SCHEMA_NAMES, _TWO_SCHEMAS, 1) + _SCHEMA_NAME_DELTA

    parsed = _parse_schema_body(
        _patched_schema_body(_TWO_SCHEMA_NAMES, _TWO_SCHEMAS, [(at, _INDEX_OF_OTHER_SCHEMA)])
    )

    assert sorted(parsed.schemas) == ["SynthSchema"]
    assert [(w.code, w.subject) for w in parsed.warnings] == [
        (usmap.WARN_UNRESOLVED_NAME, "schema-1")
    ]


def test_a_healthy_schema_section_stays_silent() -> None:
    """The negative control for every subject this section split.

    Two distinctly named schemas with resolvable indices must produce NOTHING.
    Without it, a fix that flagged unconditionally would satisfy every assertion
    above.
    """
    parsed = _parse_schema_body(
        _shipped_body(names=_TWO_SCHEMA_NAMES, enums=[], schemas=_TWO_SCHEMAS)
    )

    assert sorted(parsed.schemas) == [_OTHER_SCHEMA, "SynthSchema"]
    assert parsed.warnings == ()


def test_the_repeated_schema_name_is_flagged_at_its_own_position() -> None:
    """CS-437. The positional control the duplicate-schema subject lacked.

    ``_read_schemas`` builds this subject from ``position`` like every other
    site in the module, but the fixture that reaches it held two schemas whose
    duplicate landed at position 1 and asserted nothing about the subject at
    all. The repeat here is the THIRD schema, so a subject built from a literal
    rather than from ``position`` names a schema that did not repeat.

    The surviving definition is asserted to be the LATER one, by a property type
    the earlier definition does not carry, so the warning's account of what
    happened is checked rather than just its existence.
    """
    parsed = _parse_schema_body(
        _shipped_body(names=_TWO_SCHEMA_NAMES, enums=[], schemas=_DUPLICATE_SCHEMAS)
    )

    assert sorted(parsed.schemas) == [_OTHER_SCHEMA, "SynthSchema"]
    assert [e.type_id for e in parsed.schemas["SynthSchema"].properties] == [_TYPE_BOOL]
    assert parsed.body_consumed == parsed.container.compressed_size
    assert [(w.code, w.subject) for w in parsed.warnings] == [
        (usmap.WARN_DUPLICATE_SCHEMA, "schema-2")
    ]


# ---------------------------------------------------------------------------
# 14 - CS-435: a name whose bytes are not UTF-8 is FLAGGED, not SUBSTITUTED
#
# THE FOURTH INSTANCE OF ONE SHAPE, after CS-417, CS-419 and CS-431: a docstring
# claiming a loss is reported beside code that reports nothing. ``_Reader.text``
# decoded with ``errors="replace"`` while saying "unknown content is flagged and
# skipped rather than made fatal", and the flag half did not exist.
#
# WHY SUBSTITUTION IS THE WORSE HALF OF NON-NEGOTIABLE 7 RATHER THAN THE
# TOLERATED ONE. Replacement does not lose the name, it INVENTS a different one:
# the schema table gains a key nothing will ever look up, the body consumes
# cleanly, and ``warnings`` is empty. Downstream of the oracle, a class that IS
# modelled then answers "unmodelled" - a confident wrong answer, which is the
# "never silently wrong" half, not the "never fatal" half.
#
# WHY THE MODULE FLAGS AND CONTINUES RATHER THAN RAISING, which is the choice
# this section pins. The record cursors in clockspeed/save/header.py and
# clockspeed/save/objects.py RAISE on an undecodable string. A third decode site
# in the same layer does not: objects._payload_text returns None, and its
# docstring states the discriminator - raise where the grammar is MEASURED and a
# failure is a real defect, tolerate where the content is UNMEASURED.
#
# BLAST RADIUS SETTLES IT, and the mechanism is the CACHE. Those two raising
# sites cost the one save being read. usmap.cached_usmap parses the installed
# file at most once into a module-level cache, and world._resolve_property_map
# turns a UsmapError from it into a WorldLoadError at STAGE_USMAP. One bad byte
# in the shipped name table would therefore end every world load on the machine
# that does not supply its own mapping. Not early, either: the measured call
# order in world.load_world_from_bytes is parse_header, decompress_body, then
# the mapping, so a save whose own bytes read perfectly is still refused at the
# last step. test_an_undecodable_name_leaves_the_rest_of_the_mapping_readable is
# the assertion that choice is accountable to.
#
# THE SENTENCE ABOVE IS THE REPAIRED ONE. The first build of CS-435 wrote this
# justification around "world._resolve_usmap", a symbol that has never existed,
# and claimed the stage was reached before the save's bytes were touched, which
# the call order refutes. The conclusion survived both errors; the premise and
# the symbol did not. Section 15 fences the symbol half by machine.
#
# THE UNDECODABLE POSITION IS MADE UNRESOLVABLE rather than given a placeholder
# name, so it routes into the flag-and-skip machinery sections 7, 11 and 13
# already built and already grade. Nothing is ever published under a fabricated
# key, which is what the acceptance asks for.
# ---------------------------------------------------------------------------

#: A five-byte run that is not valid UTF-8 in any position: 0xFF and 0xFE are
#: never legal lead bytes and none of the five is a legal continuation byte.
_UNDECODABLE_BYTES = b"\xff\xfe\xfd\xfc\xfb"

#: The ASCII stand-in written first and overwritten byte for byte by the run
#: above. Same width, so no offset downstream of the name table moves.
_STAND_IN = "Undec"

#: What ``errors="replace"`` produced before CS-435 - one U+FFFD per bad byte.
#: Written as an escape so this file stays 7-bit ASCII (non-negotiable 4).
_SUBSTITUTED = "\ufffd" * len(_UNDECODABLE_BYTES)

#: Name tables for the fixtures below. The stand-in sits at position 0 in the
#: first and at position 1 in the second, which is what the positional control
#: needs.
_UNDECODABLE_FIRST = [_STAND_IN, "Alpha", "SynthSchema"]
_UNDECODABLE_SECOND = ["Alpha", _STAND_IN, "SynthSchema"]

#: The stand-in used at every name index a mapping can carry: an enum's own
#: name and its member, and a schema's own name, its super and its property.
_ALL_SITES_ENUMS = [(_STAND_IN, [_STAND_IN])]
_ALL_SITES_SCHEMAS: list[tuple[str, str | None, list[tuple[str, int]]]] = [
    (_STAND_IN, _STAND_IN, [(_STAND_IN, _TYPE_INT)])
]

#: How many warnings the all-sites fixture must raise: the undecodable name
#: itself, plus one per resolving site.
_ALL_SITES_WARNINGS = 6


def _name_text_offset(names: list[str], position: int) -> int:
    """Byte offset of name ``position``'s TEXT inside a body's name table.

    The uint32 name count, then each earlier name's uint8 length byte and its
    bytes, then this name's own length byte.
    """
    return 4 + sum(1 + len(text.encode("utf-8")) for text in names[:position]) + 1


def _with_undecodable_name(body: bytes, names: list[str], position: int) -> bytes:
    """``body`` with name ``position``'s stand-in overwritten by bad bytes.

    The stand-in is ASSERTED at the offset before the overwrite, for the reason
    :func:`_patched_body` gives: a patch that lands on the wrong offset leaves
    every test built on it green while testing nothing. The run is the same
    width as the stand-in, so the length byte stays correct and every later
    offset is unmoved.
    """
    assert names[position] == _STAND_IN, "the patched position does not hold the stand-in"
    at = _name_text_offset(names, position)
    width = len(_UNDECODABLE_BYTES)
    found = body[at : at + width]
    assert found == _STAND_IN.encode("ascii"), (
        f"byte {at} does not hold the stand-in; the patch would land on the wrong field"
    )
    return body[:at] + _UNDECODABLE_BYTES + body[at + width :]


def _assert_nothing_was_substituted(parsed: usmap.PropertyMap) -> None:
    """No collection anywhere in the mapping carries a replaced name.

    THE POINT OF THE ITEM, asserted as one helper because every fixture below
    needs it: the defect was not a lost name, it was an INVENTED one, and an
    invented name shows up as a key nothing will look up rather than as an
    absence anything reports.
    """
    assert _SUBSTITUTED not in parsed.names
    assert not any(_SUBSTITUTED in name for name in parsed.names)
    assert not any(_SUBSTITUTED in name for name in parsed.enums)
    assert not any(_SUBSTITUTED in name for name in parsed.schemas)
    for schema in parsed.schemas.values():
        assert _SUBSTITUTED not in (schema.super_name or "")
        assert not any(_SUBSTITUTED in entry.name for entry in schema.properties)


def test_an_undecodable_name_is_flagged_rather_than_silently_substituted() -> None:
    """CS-435 acceptance, pinned in both directions against a clean name.

    The two bodies differ ONLY inside the five bytes of one name. One holds
    ASCII; the other holds a run that is not UTF-8. Before the fix both parsed,
    both consumed the body to its final byte, and both reported no warning at
    all - so whether the undecodable one is FLAGGED is the entire difference
    between them, exactly as it was in sections 7 and 11.

    Both directions are asserted. A test that only checked the warning fires
    would pass just as happily against an implementation that flagged every
    name, the clean one included, and that distinguishes nothing.
    """
    names = _UNDECODABLE_FIRST
    schemas: list[tuple[str, str | None, list[tuple[str, int]]]] = [
        ("SynthSchema", None, [(_STAND_IN, _TYPE_INT), ("Alpha", _TYPE_BOOL)])
    ]
    clean_body = _shipped_body(names=names, enums=[], schemas=schemas)
    broken_body = _with_undecodable_name(clean_body, names, 0)
    at = _name_text_offset(names, 0)

    differing = {
        offset
        for offset, (left, right) in enumerate(zip(clean_body, broken_body, strict=True))
        if left != right
    }
    assert differing
    assert differing <= set(range(at, at + len(_UNDECODABLE_BYTES)))

    clean = _parse_schema_body(clean_body)
    broken = _parse_schema_body(broken_body)

    # The clean name decodes, is published, and is silent: the negative control
    # that gives every assertion below its meaning.
    assert clean.names == tuple(names)
    assert [entry.name for entry in clean.schemas["SynthSchema"].properties] == [_STAND_IN, "Alpha"]
    assert clean.warnings == ()

    # The undecodable one is flagged under its own code, naming the position in
    # the name table. Asserted as what IS there rather than as an absence.
    assert usmap.WARN_UNDECODABLE_NAME in {w.code for w in broken.warnings}
    assert (usmap.WARN_UNDECODABLE_NAME, "name-0") in [(w.code, w.subject) for w in broken.warnings]
    # And nothing anywhere in the result was invented from the bad bytes.
    _assert_nothing_was_substituted(broken)
    assert broken.body_consumed == broken.container.compressed_size


def test_an_undecodable_name_leaves_the_rest_of_the_mapping_readable() -> None:
    """Flagged and SKIPPED, never FATAL - and the control on raise-versus-flag.

    The undecodable name is referenced by NOTHING here, so every other name,
    enum and schema in the mapping is readable and must come back whole. A
    module that answered a decode failure by raising would lose all of it, and
    a usmap is the oracle for the whole save library rather than for one save.
    This assertion is what that choice is accountable to.
    """
    names = _UNDECODABLE_FIRST
    schemas: list[tuple[str, str | None, list[tuple[str, int]]]] = [
        ("SynthSchema", None, [("Alpha", _TYPE_INT)])
    ]
    body = _with_undecodable_name(_shipped_body(names=names, enums=[], schemas=schemas), names, 0)

    parsed = _parse_schema_body(body)

    assert sorted(parsed.schemas) == ["SynthSchema"]
    assert [entry.name for entry in parsed.schemas["SynthSchema"].properties] == ["Alpha"]
    assert parsed.body_consumed == parsed.container.compressed_size
    assert [(w.code, w.subject) for w in parsed.warnings] == [
        (usmap.WARN_UNDECODABLE_NAME, "name-0")
    ]
    _assert_nothing_was_substituted(parsed)


def test_the_five_healthy_resolving_sites_each_report_an_undecodable_name() -> None:
    """Five sites named one by one, because the general claim was measurably false.

    A warning that FIRES is not a warning that SAYS SOMETHING TRUE, which is
    what CS-430 shipped. THE FIRST BUILD OF CS-435 SHIPPED IT AGAIN: this test
    was originally named for every index resolving to an undecodable name while
    exercising only the five sites below, and the warning detail beside it made
    the same universal claim. Section 15 pins four measured paths that refute it
    and the detail no longer makes it.

    What survives is exactly this - the fixture points all five resolving sites
    at one undecodable name, on the happy path where nothing else has gone
    wrong: an enum's own name and its member, and a schema's own name, its super
    and its property. Each is asserted to produce its own unresolved warning.
    Read the name as naming these five, and nothing beyond them.

    The two empty collections are the other half of the same claim: with every
    site unresolvable, nothing at all may be published, and before the fix the
    enum and the schema were both published under a fabricated key.
    """
    names = _UNDECODABLE_FIRST
    body = _with_undecodable_name(
        _shipped_body(names=names, enums=_ALL_SITES_ENUMS, schemas=_ALL_SITES_SCHEMAS),
        names,
        0,
    )

    parsed = _parse_schema_body(body)

    assert parsed.enums == {}
    assert parsed.schemas == {}
    assert parsed.body_consumed == parsed.container.compressed_size
    assert [(w.code, w.subject) for w in parsed.warnings] == [
        (usmap.WARN_UNDECODABLE_NAME, "name-0"),
        (usmap.WARN_UNRESOLVED_NAME, "enum-0-member"),
        (usmap.WARN_UNRESOLVED_NAME, "enum-0"),
        (usmap.WARN_UNRESOLVED_NAME, "schema-0-super"),
        (usmap.WARN_UNRESOLVED_NAME, "schema-0-property"),
        (usmap.WARN_UNRESOLVED_NAME, "schema-0"),
    ]
    assert [w.count for w in parsed.warnings] == [1] * _ALL_SITES_WARNINGS
    _assert_nothing_was_substituted(parsed)


def test_an_undecodable_name_displaces_no_other_conditions_detail() -> None:
    """The CS-419 regression shape, checked against the warning added here.

    ``_WarningLog`` aggregates by ``(code, subject)`` and KEEPS THE FIRST DETAIL
    SEEN. The name table is read BEFORE the enums and the schemas, so a new
    warning sharing a key with any later condition would replace that
    condition's true sentence with this one - the exact failure CS-419's first
    round shipped.

    No literal sentence is asserted. Each condition's detail is compared against
    the detail THAT SAME CONDITION produces when it happens without an
    undecodable name in the table, so the test pins the behaviour and cannot be
    satisfied by rewording, nor go red because of it.
    """
    names = _UNDECODABLE_FIRST
    body = _with_undecodable_name(
        _shipped_body(names=names, enums=_ALL_SITES_ENUMS, schemas=_ALL_SITES_SCHEMAS),
        names,
        0,
    )
    together = _parse_schema_body(body)

    enum_name_at = (_enum_name_offset(_ENUM_NAMES, _ONE_ENUM, 0), _INDEX_OF_SYNTH_ENUM)
    enum_member_at = (_enum_member_offset(_ENUM_NAMES, _ONE_ENUM, 0, 1), _INDEX_OF_MEMBER_ONE)
    alone = {
        "enum-0": _parse_enum_body(_patched_enum_body(_ENUM_NAMES, _ONE_ENUM, [enum_name_at])),
        "enum-0-member": _parse_enum_body(
            _patched_enum_body(_ENUM_NAMES, _ONE_ENUM, [enum_member_at])
        ),
    }
    base = _schema_super_offset(_SCHEMA_NAMES, _ONE_SCHEMA, 0)
    for subject, delta, anchor in (
        ("schema-0", _SCHEMA_NAME_DELTA, _INDEX_OF_SYNTH_SCHEMA),
        ("schema-0-super", 0, _ALL_BITS_SET),
        ("schema-0-property", _PROPERTY_NAME_DELTA, _INDEX_OF_ALPHA),
    ):
        alone[subject] = _parse_schema_body(
            _patched_schema_body(_SCHEMA_NAMES, _ONE_SCHEMA, [(base + delta, anchor)])
        )

    for subject, isolated in alone.items():
        assert _detail_for(together, usmap.WARN_UNRESOLVED_NAME, subject) == _detail_for(
            isolated, usmap.WARN_UNRESOLVED_NAME, subject
        ), subject


def test_the_flagged_name_is_flagged_at_its_own_position() -> None:
    """The positional control this section's new subject needs from the start.

    ``name-N`` is built by the same interpolation as every other subject in the
    module, and CS-437 measured what happens when one of those has no two-item
    fixture. The undecodable name here is the SECOND one, and the first name is
    asserted to have decoded, so a subject built from a literal rather than from
    the position names a name that is intact.
    """
    names = _UNDECODABLE_SECOND
    schemas: list[tuple[str, str | None, list[tuple[str, int]]]] = [
        ("SynthSchema", None, [("Alpha", _TYPE_INT)])
    ]
    body = _with_undecodable_name(_shipped_body(names=names, enums=[], schemas=schemas), names, 1)

    parsed = _parse_schema_body(body)

    assert parsed.names[0] == "Alpha"
    assert [(w.code, w.subject) for w in parsed.warnings] == [
        (usmap.WARN_UNDECODABLE_NAME, "name-1")
    ]
    _assert_nothing_was_substituted(parsed)


def test_two_undecodable_names_are_flagged_separately_rather_than_merged() -> None:
    """Each bad name is its own subject, so a count of two is never a total.

    ``_WarningLog`` merges by ``(code, subject)``, so a subject that did not
    carry the position would report two losses as one warning counted twice and
    name the wrong position for at least one of them.
    """
    names = [_STAND_IN, "Alpha", _STAND_IN]
    schemas: list[tuple[str, str | None, list[tuple[str, int]]]] = [
        ("Alpha", None, [("Alpha", _TYPE_INT)])
    ]
    body = _shipped_body(names=names, enums=[], schemas=schemas)
    body = _with_undecodable_name(body, names, 0)
    body = _with_undecodable_name(body, names, 2)

    parsed = _parse_schema_body(body)

    assert [(w.code, w.subject) for w in parsed.warnings] == [
        (usmap.WARN_UNDECODABLE_NAME, "name-0"),
        (usmap.WARN_UNDECODABLE_NAME, "name-2"),
    ]
    assert [w.count for w in parsed.warnings] == [1, 1]
    assert sorted(parsed.schemas) == ["Alpha"]
    _assert_nothing_was_substituted(parsed)


def test_a_name_table_that_decodes_cleanly_stays_silent() -> None:
    """The negative control for the code this section adds.

    Without it, a fix that flagged every name would satisfy every assertion
    above. The stand-in is present and UNPATCHED here, so this is the same
    fixture the acceptance test compares against rather than a different one.
    """
    names = _UNDECODABLE_FIRST

    parsed = _parse_schema_body(
        _shipped_body(names=names, enums=_ALL_SITES_ENUMS, schemas=_ALL_SITES_SCHEMAS)
    )

    assert parsed.names == tuple(names)
    assert parsed.enums == {_STAND_IN: (_STAND_IN,)}
    assert sorted(parsed.schemas) == [_STAND_IN]
    assert parsed.warnings == ()


# ---------------------------------------------------------------------------
# 15 - CS-435 repair: this module's own prose is graded by machine
#
# WHY THIS SECTION EXISTS. CS-435's first build shipped a warning DETAIL making
# a universal claim about the module - "every index resolving to it is flagged
# unresolved" - and measurement refuted it. The project already runs a fence for
# absolute claims and it could not have caught this one: that fence reads
# docstrings, comments and assert messages, and A WARNING DETAIL IS A CALL
# ARGUMENT. So the fence for that shape lives here, beside the module it grades.
#
# THE SECOND FENCE IS FOR A CITED SYMBOL. The same build justified its design by
# naming ``world._resolve_usmap``, which has never existed in this tree. A
# symbol that does not resolve is the cheapest lie there is to catch by machine,
# and nothing in the suite was catching it.
#
# THE COUNTER-EXAMPLES ARE PINNED AS TESTS rather than described in a comment,
# for the reason the deleted sentence demonstrates: a hole that lives only in
# prose is a hole the next author to read the file closes in prose.
# ---------------------------------------------------------------------------

#: Short module name to dotted path, for the citation fence. A citation naming a
#: module absent from this map fails the test rather than being skipped, so a
#: new sibling cannot be cited into a blind spot.
_CITED_MODULES = {
    "header": "clockspeed.save.header",
    "locate": "clockspeed.data.locate",
    "objects": "clockspeed.save.objects",
    "usmap": "clockspeed.save.usmap",
    "world": "clockspeed.save.world",
}

#: Matches ``module.symbol`` for the siblings above. ``module.py`` is a FILE
#: reference rather than a symbol citation and is dropped below.
_CITATION = re.compile(r"\b(" + "|".join(_CITED_MODULES) + r")\.(_?[A-Za-z][A-Za-z0-9_]*)")

#: Words that turn a warning detail into a claim about OTHER sites. STATED AS A
#: FLOOR, NOT A GRAMMAR: a universal phrased around this list still gets through,
#: and this sentence is the honest limit rather than a promise of completeness.
#: "nothing" and "any" are deliberately absent: each appears today in a detail
#: quantifying over something other than this module's resolution sites - the
#: trailing-section and the unknown-version detail respectively. "none" is held
#: out alongside them as the same kin, not because it appears anywhere today.
#: Widening the list to cover the three is separate work with its own
#: measurement.
_SITE_QUANTIFIERS = frozenset({"every", "all", "each", "always", "never", "only"})

#: Bytes cut off the end of an enum-section body to strand the member run: one
#: uint32 member index plus the two bytes before it, so the read runs off the
#: end rather than landing on a short but well formed entry.
_ENUM_TRUNCATION = 6


def _module_source() -> str:
    """The parser module's own source text.

    The path is read and never rendered. The assertions below quote the
    offending SENTENCE, which is authored prose, and never the location, which
    is an absolute path under a home directory (non-negotiable 3).
    """
    return Path(usmap.__file__).read_text(encoding="utf-8")


def _flattened(node: ast.expr) -> str:
    """The literal text of a string node, with any interpolation as a blank."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        # An f-string's literal runs only. A ``{...}`` field becomes a space, so
        # two literal runs cannot be joined into a word that neither contains.
        return " ".join(
            part.value
            for part in node.values
            if isinstance(part, ast.Constant) and isinstance(part.value, str)
        )
    return ""


def _warning_details() -> list[tuple[str, str]]:
    """Every ``(code, detail)`` the parser module passes to ``_WarningLog.add``.

    Derived from the module's own syntax tree rather than from a list kept here,
    so a detail added tomorrow is graded without anyone remembering to add it.
    """
    found: list[tuple[str, str]] = []
    for node in ast.walk(ast.parse(_module_source())):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "add":
            continue
        if len(node.args) < _THREE or not isinstance(node.args[0], ast.Name):
            continue
        found.append((getattr(usmap, node.args[0].id), _flattened(node.args[2])))
    return found


def _declared_warning_codes() -> set[str]:
    """Every ``WARN_*`` value the parser module defines."""
    return {
        value
        for name, value in vars(usmap).items()
        if name.startswith("WARN_") and isinstance(value, str)
    }


def test_no_warning_detail_claims_what_happens_at_another_site() -> None:
    """CS-435 repair. The fence the absolute-claims scan structurally cannot be.

    A warning detail describes ONE flagged position. The moment it quantifies
    over the module's other resolution sites it becomes a measurement of the
    whole module restated in prose with nothing checking it - and CS-435's first
    build shipped exactly that, and every counter-example that refuted it is
    pinned below rather than described.

    THE POPULATION IS DERIVED AND ITS LIVENESS IS ASSERTED. Every code the module
    declares must appear among the details actually extracted, so this cannot
    pass by parsing nothing or by quietly missing a call site.
    """
    details = _warning_details()

    assert {code for code, _ in details} == _declared_warning_codes()

    for code, detail in details:
        offending = sorted(set(re.findall(r"[a-z]+", detail.lower())) & _SITE_QUANTIFIERS)
        assert not offending, f"{code} detail quantifies over other sites {offending}: {detail}"


def test_every_sibling_symbol_cited_in_the_parser_module_resolves() -> None:
    """CS-435 repair. A justification may not cite a symbol that does not exist.

    ``world._resolve_usmap`` was cited as the mechanism turning a parse failure
    into a load failure. The function is ``world._resolve_property_map``, and the
    cited name appears nowhere in the tree except in the prose citing it. A
    reader checking that reasoning would have gone looking for a symbol that is
    not there, and a design decision nobody can re-derive is a decision this
    project has already lost more than once.

    The population is derived from the module text and asserted non-empty, so
    deleting every citation fails this rather than satisfying it.
    """
    citations = {
        (module, symbol) for module, symbol in _CITATION.findall(_module_source()) if symbol != "py"
    }

    assert citations, "no sibling citation was found; the pattern has stopped matching"
    for module, symbol in sorted(citations):
        assert module in _CITED_MODULES, f"{module} is cited but not mapped to a dotted path"
        # The boolean is taken FIRST so the module object is never an argument
        # pytest can render: its repr is an absolute path (non-negotiable 3).
        exists = hasattr(importlib.import_module(_CITED_MODULES[module]), symbol)
        assert exists, f"{module}.{symbol} is cited but does not exist"


def test_the_audit_reader_refuses_exactly_what_the_parser_refuses() -> None:
    """CS-435 residual. The second decoder in this file agreed with nothing.

    ``_audit_read_names`` reads the shipped name table independently, and it
    decoded with ``errors="replace"`` after the parser stopped doing so. That is
    not merely a leftover. ``_audit_rebuild`` builds its index table from ITS OWN
    names, so a substituted name resolves to the same index the file holds, the
    rebuilt entry matches byte for byte, and the audit reports IDENTICAL - a
    false green in the one test whose whole purpose is to grade the builder
    against the game.

    Both decoders are put to the same bytes here, and neither may accept what
    the other rejects.
    """
    clean = _shipped_body(names=_UNDECODABLE_FIRST, enums=[], schemas=[])
    broken = _with_undecodable_name(clean, _UNDECODABLE_FIRST, 0)

    for body, parser_flags_it in ((clean, False), (broken, True)):
        parsed = _parse_schema_body(body)
        flagged = usmap.WARN_UNDECODABLE_NAME in {w.code for w in parsed.warnings}
        assert flagged is parser_flags_it

        try:
            _audit_read_names(_BodyCursor(body))
        except UnicodeDecodeError:
            audit_refused = True
        else:
            audit_refused = False
        assert audit_refused is flagged, "the two decoders disagree about these bytes"


def test_an_undecodable_property_name_behind_an_unknown_type_is_not_flagged() -> None:
    """The first counter-example to the sentence CS-435's first build shipped.

    ``_read_schema`` tests the type byte BEFORE it tests the property name, and
    the unknown-type branch consumes the entry with ``continue``. So an index
    that resolved to an undecodable name is dropped with no unresolved warning
    against it. The loss is not silent overall - the undecodable name and the
    unknown type are both flagged - but the PER-SITE attribution is gone.

    THIS ORDERING IS UNCHANGED FROM BEFORE CS-435 and is not this item's defect.
    It is the reason no universal about resolving indices is written beside the
    warning. The control below is the same fixture with a known type byte, where
    the flag does fire, so this pins an ORDERING rather than an absence.
    """
    schemas: list[tuple[str, str | None, list[tuple[str, int]]]] = [
        ("SynthSchema", None, [(_STAND_IN, _UNKNOWN_TYPE)])
    ]
    body = _with_undecodable_name(
        _shipped_body(names=_UNDECODABLE_FIRST, enums=[], schemas=schemas), _UNDECODABLE_FIRST, 0
    )

    parsed = _parse_schema_body(body)

    assert [(w.code, w.subject) for w in parsed.warnings] == [
        (usmap.WARN_UNDECODABLE_NAME, "name-0"),
        (usmap.WARN_UNKNOWN_PROPERTY_TYPE, f"type-{_UNKNOWN_TYPE}"),
    ]
    _assert_nothing_was_substituted(parsed)

    known: list[tuple[str, str | None, list[tuple[str, int]]]] = [
        ("SynthSchema", None, [(_STAND_IN, _TYPE_INT)])
    ]
    control = _parse_schema_body(
        _with_undecodable_name(
            _shipped_body(names=_UNDECODABLE_FIRST, enums=[], schemas=known),
            _UNDECODABLE_FIRST,
            0,
        )
    )

    # One byte different, and the per-site flag is back.
    assert (usmap.WARN_UNRESOLVED_NAME, "schema-0-property") in [
        (w.code, w.subject) for w in control.warnings
    ]


def test_an_undecodable_schema_name_in_a_desynchronised_entry_is_not_flagged() -> None:
    """The second counter-example, and the reason a reordering repair was refused.

    ``_read_schema`` flags an unresolvable schema NAME at the BOTTOM of the
    function, after every site that can raise. An entry that desynchronises
    therefore loses that flag entirely: the section reports the desync, and
    nothing says the lost schema's own name was the undecodable one.

    ALSO UNCHANGED FROM BEFORE CS-435. Moving the flag to the top would close
    this one, but two further sites in ``_read_enums`` cannot be closed that way
    at all - that section is not wrapped by its caller, so a desync there raises
    out of ``parse_usmap`` and publishes NO warnings whatsoever. The universal
    was deleted rather than repaired because no reordering makes it true.
    """
    schemas: list[tuple[str, str | None, list[tuple[str, int]]]] = [
        (_STAND_IN, None, [("Alpha", _TYPE_INT)])
    ]
    body = _with_undecodable_name(
        _shipped_body(names=_UNDECODABLE_FIRST, enums=[], schemas=schemas), _UNDECODABLE_FIRST, 0
    )
    name_index_at = _schema_super_offset(_UNDECODABLE_FIRST, schemas, 0) + _SCHEMA_NAME_DELTA
    (anchor,) = struct.unpack_from("<I", body, name_index_at)
    assert anchor == 0, "the offset walk does not land on the schema's own name index"

    parsed = _parse_schema_body(body[: name_index_at + 4])

    assert [(w.code, w.subject) for w in parsed.warnings] == [
        (usmap.WARN_UNDECODABLE_NAME, "name-0"),
        (usmap.WARN_DESYNCHRONISED_SECTION, "schemas"),
    ]
    assert parsed.schemas == {}


def test_an_enum_section_desync_loses_the_undecodable_names_resolving_flags() -> None:
    """The third and fourth counter-examples, which no reordering reaches.

    ``_read_schemas`` wraps its per-entry ``_read_schema`` call in a handler
    that converts a desynchronised entry into a warning. ``_read_enums`` has no
    such handler and its caller ``parse_usmap`` adds none, so a truncated enum
    section raises straight out of the parse. There is then no mapping and no
    warning list at all, and an index in that section that resolved to the
    undecodable name is reported nowhere.

    Making the deleted universal true would therefore have required the enum
    section to stop being fatal - a change to behaviour this module states
    deliberately, far outside a decoder item. Hence deletion.
    """
    enums = [("Alpha", [_STAND_IN, "Alpha"])]
    body = _with_undecodable_name(
        _shipped_body(names=_UNDECODABLE_FIRST, enums=enums, schemas=[]), _UNDECODABLE_FIRST, 0
    )

    # Intact, the member index that resolves to the undecodable name IS flagged.
    intact = _parse_enum_body(body)
    assert [(w.code, w.subject) for w in intact.warnings] == [
        (usmap.WARN_UNDECODABLE_NAME, "name-0"),
        (usmap.WARN_UNRESOLVED_NAME, "enum-0-member"),
    ]

    # Cut short inside the member run, the whole parse is fatal and flags nothing.
    with pytest.raises(usmap.UsmapFormatError):
        _parse_enum_body(body[: len(body) - _ENUM_TRUNCATION])

    # THE FOURTH PATH, the enum's OWN name rather than a member's, so the two
    # sites in this section are both pinned rather than one standing for both.
    own = [("Alpha", ["Alpha"]), (_STAND_IN, ["Alpha", "Alpha"])]
    own_body = _with_undecodable_name(
        _shipped_body(names=_UNDECODABLE_FIRST, enums=own, schemas=[]), _UNDECODABLE_FIRST, 0
    )
    assert [(w.code, w.subject) for w in _parse_enum_body(own_body).warnings] == [
        (usmap.WARN_UNDECODABLE_NAME, "name-0"),
        (usmap.WARN_UNRESOLVED_NAME, "enum-1"),
    ]
    with pytest.raises(usmap.UsmapFormatError):
        _parse_enum_body(own_body[: len(own_body) - _ENUM_TRUNCATION])


# ---------------------------------------------------------------------------
# CS-471 - THIS MODULE'S LIBRARY REACH, DECLARED.
#
# The guard is owned by ``reach_guard`` and applied across this package by
# the suite-wide test in ``test_reach_guard``, which walks the package
# directory rather than waiting to be called. Before CS-471 this module touched a library
# primitive while declaring no reach at all, and the suite had no check that
# would say so.
#
# The wording here is deliberately free of the CS-420 quantifier vocabulary,
# because two modules carrying this block sit inside that fence.
# ---------------------------------------------------------------------------

#: Helpers that genuinely reach the save library, name to why each reaches.
_GRADED_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})

#: Touches a primitive WITHOUT consuming a real save path, name to why.
#: Asserted still reaching, so a stale exemption reddens the guard.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType(
    {
        "test_the_builder_reproduces_the_shipped_bytes_it_models": (
            "reads the shipped usmap out of the auto-detected GAME INSTALL, "
            "which is publisher-owned game data rather than the save "
            "library - no save path and no account directory passes through "
            "it "
        ),
        "test_the_evidence_table_matches_what_the_rebuild_audit_measures": (
            "reads the shipped usmap out of the auto-detected GAME INSTALL, "
            "which is publisher-owned game data rather than the save "
            "library - no save path and no account directory passes through "
            "it "
        ),
        "test_the_loader_never_writes_to_the_install": (
            "builds a SYNTHETIC usmap into tmp_path and points the game-dir "
            "environment variable at it, so the install it reads is the one "
            "this test wrote "
        ),
        "test_the_real_usmap_accounts_for_its_own_length_exactly": (
            "reads the shipped usmap out of the auto-detected GAME INSTALL, "
            "which is publisher-owned game data rather than the save "
            "library - no save path and no account directory passes through "
            "it "
        ),
    }
)
