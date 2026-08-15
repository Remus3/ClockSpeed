"""Property-mapping loader: container framing, inner grammar, cache and limits.

WHAT IS MEASURED HERE AND WHAT IS BUILT
-----------------------------------------
The shipped ``FactoryGame.usmap`` inner grammar was DERIVED FROM THE BYTES for
this slice and verified by a single decisive constraint: the derived reader
consumes the real file's name, enum and schema sections and lands EXACTLY on a
four-character ASCII section tag, with every property type byte inside a
plausible range and every name index in bounds across the whole file.
``test_the_real_usmap_accounts_for_its_own_length_exactly`` is that check, and
it is the control that stops this module from being graded only by itself.

``tests/save/synthetic.py`` is used for everything its builder actually models.
Its OUTER framing is measured and is reused verbatim here through
:func:`_reframe`, which copies the builder's own magic, version and compression
bytes and only corrects the two size fields.

Its INNER grammar for ENUMS and SCHEMAS is a self-consistent placeholder - its
own docstring says so - and it does NOT match the shipped file: the builder
writes inline length-prefixed strings where the shipped format writes uint32
indices into the name table, and it has no property-type byte at all. The NAMES
section does match. So the builder is used directly wherever the two agree, and
:func:`_shipped_body` builds the sections it does not model. That helper is not
a second copy of ``build_usmap`` - it encodes a grammar ``build_usmap`` does not
implement, and the slice report files the gap.

NO REAL GAME DATA IS IN THIS FILE. Every name below is invented. The one test
that opens the shipped file SKIPS WITH A REASON when there is no install, and
asserts SHAPES ONLY - counts, offsets and widths. It binds no decoded name and
prints nothing (``tests/save/__init__.py``, non-negotiable 2).
"""

from __future__ import annotations

import struct
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
_TYPE_STRUCT = 9


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
    """Build the SHIPPED inner grammar, which ``build_usmap`` does not model.

    Derived from the shipped file and verified against it - see the module
    docstring. Enum and schema names are uint32 indices into the name table
    here, where ``build_usmap`` writes inline strings.

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
    grammar cannot land on the container's exact byte count.
    """
    game_dir, _label = resolve_game_dir()
    if game_dir is None:
        pytest.skip("no game install resolved on this machine")
    path = game_dir / "CommunityResources" / "FactoryGame.usmap"
    if not path.is_file():
        pytest.skip("the install carries no FactoryGame.usmap")

    size_on_disk = path.stat().st_size
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
