"""The save header parse, and the redaction guarantee that is the point of it.

WHAT THIS MODULE IS ACTUALLY FOR
----------------------------------
Two thirds of the tests below are privacy tests, and that ratio is correct
rather than paranoid. ``docs/adr/0007`` records that the header string block
changes COUNT AND ORDER with the header version, so a redactor aimed at a NAMED
field is defeated by a shifted field ORDER: on header versions 10 and 13 the
THIRD string is the operator's world name, and on header version 14 the third
string is the options string. A probe leaked a world name by exactly that
off-by-one during the session that produced the ADR.

So the parse itself is a few dozen lines of offset arithmetic, and the thing
that has to be PROVEN is that no header string reaches any surface a human or a
log can read.

THE PLANTED-MARKER TEST IS THE LOAD-BEARING ONE
-------------------------------------------------
``test_planted_markers_never_reach_any_surface`` builds a header whose save
name, options string and session name each carry a distinctive invented marker,
then drives every success and every failure path and asserts the marker appears
in none of: ``str(exc)``, ``exc.args``, ``repr(exc)``, ``exc.__notes__``, the
formatted traceback, ``repr(SaveHeader)``, any field of ``SaveHeader``, or any
warning. It is parameterized across header versions 10, 13 and 14 precisely
because the ADR's failure mode is a version-dependent ORDER - a parser that
reads the header-14 layout out of a header-10 file lands a marker in
``map_name``, and only a cross-version run sees it.

That converts "redacts by default" from a claim in a docstring into a check
that fails loudly.

THE TAXONOMY GATE IS STATIC, NOT SAMPLED
------------------------------------------
``test_every_error_class_takes_only_taxonomy_safe_parameters`` introspects the
``__init__`` of every error class in the module and asserts each parameter is
drawn from a fixed vocabulary of names and is annotated ``int`` or ``str``, and
that no class accepts ``*args`` or ``**kwargs``. A sampled test only proves the
raise sites it happened to reach; this one proves there is no PARAMETER through
which raw bytes, a decoded string or a path could travel, at any raise site,
including ones written later.

INDEPENDENCE FROM THE FIXTURE, DELIBERATELY
---------------------------------------------
``clockspeed/save/header.py`` imports nothing from ``tests/save/synthetic.py``
and spells its own copy of every measured constant - the version numbers, the
tail size, the token length. Both are independent encodings of the measurement
that ``BOOTSTRAP.md`` section 2.4 owns. Sharing the constants would make the
suite a restatement of the builder's own opinion, which is the parallel-fixture
failure class named in ``memory/test-quality-failure-classes.md``.

WHAT IS DELIBERATELY NOT ASSERTED HERE, AND WHY
------------------------------------------------
Three of the five file-scope points in ``synthetic.TRUNCATION_BOUNDARIES`` land
PAST the end of the header - at magic+2, magic+20 and magic+53. Only the first
of those is reachable by this layer: the header's seam promise is that
``body_offset`` is the absolute offset of the chunk magic, so the parse checks
that four bytes exist there and fails when they do not. At magic+20 and
magic+53 the header is COMPLETE AND CORRECT and the damage is entirely inside
the chunk frame, which ``clockspeed/save/chunks.py`` owns. This module asserts
that those two parse cleanly rather than pretending the header can see them -
a header parser that validated the chunk frame would be reaching past its
neighbour, which BOOTSTRAP.md section 6 calls a design bug.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import struct
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final

import pytest

from clockspeed.save import header as header_module
from clockspeed.save.header import (
    HeaderError,
    HeaderFormatError,
    HeaderReadError,
    HeaderStrings,
    HeaderTruncatedError,
    HeaderWarning,
    PersonalDataOptInRequiredError,
    SaveHeader,
    UnsupportedHeaderVersionError,
    masked_token,
    parse_header,
    read_header,
    reveal_strings,
)
from tests.save import synthetic, test_properties

# ---------------------------------------------------------------------------
# Planted markers
# ---------------------------------------------------------------------------

#: Three invented needles, one per PII-bearing header string. They are single
#: tokens with no spaces or punctuation so a substring search for them cannot
#: be defeated by a renderer that re-wraps or escapes a longer phrase.
MARKER_SAVE_NAME: Final = "MarkerAlphaSaveNameNeedle"
MARKER_OPTIONS: Final = "MarkerBravoOptionsNeedle"
MARKER_SESSION: Final = "MarkerCharlieSessionNeedle"

MARKERS: Final = (MARKER_SAVE_NAME, MARKER_OPTIONS, MARKER_SESSION)

#: Header versions whose string block this module walks. Spelled here rather
#: than imported from the parser, so a parser that dropped a version cannot
#: quietly shrink its own test matrix.
HEADER_10: Final = 10
HEADER_13: Final = 13
HEADER_14: Final = 14
HEADER_VERSIONS: Final = (HEADER_10, HEADER_13, HEADER_14)

#: The one header version that emits a save name. Restated for the same reason.
VERSION_WITH_SAVE_NAME: Final = HEADER_14

#: The save version SAVE_CROSS pairs with header 14 - a pair in no real file.
CROSS_SAVE_VERSION: Final = 36

#: The measured 22-character base64url identifier length.
TOKEN_LENGTH: Final = 22

#: Reads 40 on all 14 measured saves, which is what independently anchors the
#: position of the unverified int8 immediately before it (ADR 0007 item 5).
EDITOR_OBJECT_VERSION: Final = 40

#: Offset of the first string's int32 count. Three int32 version fields precede
#: it on every header version.
FIRST_STRING_COUNT_OFFSET: Final = 12

#: How many header strings each parser function is allowed to DECODE, and how
#: many it must step over. The default parse may decode only the map name and
#: the identifier; the opt-in path decodes all four string slots.
DECODED_IN_PARSE: Final = 2
SKIPPED_IN_PARSE: Final = 4
DECODED_IN_REVEAL: Final = 4


def _marker_header_kwargs(header_version: int) -> dict[str, object]:
    """Build the header kwargs for a marker-bearing fixture.

    Args:
        header_version: 10, 13 or 14.

    Returns:
        Keyword arguments for the synthetic builder. The save name is supplied
        on every version; the builder emits it only on header 14, which is the
        behaviour under test.
    """
    return {
        "header_version": header_version,
        "save_version": 60,
        "save_name": MARKER_SAVE_NAME,
        "options": "?" + MARKER_OPTIONS + "=1",
        "session_name": MARKER_SESSION,
    }


def _marker_blob(header_version: int) -> bytes:
    """Build a whole marker-bearing save.

    Args:
        header_version: 10, 13 or 14.

    Returns:
        The blob, header plus one framed chunk.
    """
    return synthetic.build_save(header_kwargs=_marker_header_kwargs(header_version))


def _marker_header_length(header_version: int) -> int:
    """Length of the marker fixture's header, so a test can cut inside it.

    Args:
        header_version: 10, 13 or 14.

    Returns:
        The byte length of the header alone.
    """
    kwargs = _marker_header_kwargs(header_version)
    return len(synthetic.build_header(**kwargs))  # type: ignore[arg-type]


def _spelling_of(marker: str, blob: bytes) -> bytes | None:
    """Which spelling of ``marker`` the fixture carries, or None for neither.

    Unreal writes a string as UTF-8 with a positive count or UTF-16-LE with a
    negative one, so there are two candidates and no third. An arm uses this to
    take its needle FROM THE FIXTURE rather than assuming a spelling - assuming
    is what made the arms this item exists to fix measure the wrong encoding.

    Args:
        marker: The planted marker, in its plain text.
        blob: The fixture bytes.

    Returns:
        The spelling found, narrow preferred when somehow both are present, or
        None if the fixture carries neither.
    """
    for candidate in (marker.encode("utf-8"), marker.encode("utf-16-le")):
        if candidate in blob:
            return candidate
    return None


def _markers_present_in(blob: bytes, header_version: int) -> tuple[str, ...]:
    """Which markers the fixture actually encodes at this header version.

    Header versions 10 and 13 carry no save name, so its marker is never in
    the bytes and asserting its absence downstream would pass vacuously. This
    keeps the marker test honest about what it is actually proving.

    PRESENCE IS ASKED PER MARKER ACROSS BOTH SPELLINGS (CS-964). It used to ask
    ``marker.encode("utf-8") in blob``, which reddened this helper the moment a
    fixture was spliced to its wide spelling - two of the three markers went
    missing as far as it could tell. A single ``encoding`` parameter would be
    the wrong shape, because ``_wide_marker_blob`` is MIXED on purpose: it
    splices the options and session fields, the two a person types, and leaves
    the save name narrow.

    The PLAIN TEXT is still what comes back, because :func:`_assert_free_of`
    searches every spelling a renderer prints, so its callers go on handing it
    plain markers.

    Args:
        blob: The fixture bytes.
        header_version: 10, 13 or 14.

    Returns:
        The markers genuinely encoded in ``blob``.
    """
    present = tuple(marker for marker in MARKERS if _spelling_of(marker, blob) is not None)
    expected = len(MARKERS) if header_version >= VERSION_WITH_SAVE_NAME else len(MARKERS) - 1
    assert len(present) == expected, (
        f"marker fixture for header {header_version} encodes {len(present)} markers,"
        f" expected {expected}"
    )
    return present


# ---------------------------------------------------------------------------
# Surface collection - every place a value could escape to
# ---------------------------------------------------------------------------


def _exception_surfaces(exc: BaseException) -> list[str]:
    """Every rendering of an exception a human or a log could ever see.

    Args:
        exc: The raised exception.

    Returns:
        The renderings, as strings.
    """
    return [
        str(exc),
        repr(exc),
        repr(exc.args),
        repr(getattr(exc, "__notes__", ())),
        "".join(traceback.format_exception(exc)),
    ]


def _value_surfaces(value: object) -> list[str]:
    """Every rendering of a value, recursing into dataclasses and sequences.

    Args:
        value: Anything a parse returned.

    Returns:
        The renderings, as strings.
    """
    out = [repr(value), str(value)]
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        for entry in dataclasses.fields(value):
            out.extend(_value_surfaces(getattr(value, entry.name)))
    elif isinstance(value, (tuple, list)):
        for item in value:
            out.extend(_value_surfaces(item))
    return out


def _assert_free_of(surfaces: list[str], needles: tuple[str, ...], where: str) -> None:
    """Assert no needle appears in any surface, IN ANY SPELLING A RENDERER PRINTS.

    THE ASCII-ONLY VERSION WENT GREEN OVER A WIDE RAW SLICE, measured by an
    adversary against this very helper: ``_value_surfaces`` recurses arbitrary
    field types and emits ``repr(value)``, and ``repr(bytes)`` is a string by
    type and raw bytes by content. So a parser carrying a UTF-16-LE slice - the
    spelling a session name or a player display name actually has on a real save
    - leaked through a sweep that reported clean.

    EVERY HEADER PRIVACY ARM FUNNELS THROUGH HERE, which is why the spelling set
    is widened at this one chokepoint instead of in ten arms separately. The
    spelling list itself lives in ``test_properties`` so the frame-local oracle
    and this one cannot drift apart.

    Args:
        surfaces: Renderings to search.
        needles: The planted markers, in their plain text.
        where: A label naming the path under test, for the failure message.

    Raises:
        AssertionError: A needle leaked, in any of its rendered spellings.
    """
    for needle in needles:
        for spelling in test_properties._rendered_spellings(needle):  # noqa: SLF001
            for surface in surfaces:
                assert spelling not in surface, (
                    f"planted marker leaked via {where} - as {spelling!r}"
                )


def test_the_surface_sweep_is_not_blind_to_a_wide_encoded_raw_slice() -> None:
    """MEASURED BY AN ADVERSARY: THE WIDE FIELD MAKES THIS SUITE'S WIDEST ARM GREEN.

    :func:`_value_surfaces` recurses into arbitrary dataclass field types and
    emits ``repr(value)`` for each. ``repr(bytes)`` is a ``str`` BY TYPE and raw
    bytes BY CONTENT, so the survey's rule - "a decoded-string oracle sees ASCII
    at either encoding" - does not hold here, and this is the counter-example it
    was refuted by.

    WHAT REGRESSION THIS GUARDS. The header module's design is that the bytes
    never become Python strings at all; the mutant that matters is a parser that
    stops stepping over a slice and starts CARRYING it. Measured: that mutant
    dies against a narrow field and SURVIVES against a wide one, because the
    ASCII needle cannot be seen in the wide rendering. An ``isascii()`` gate does
    not help - the escapes are ASCII themselves.

    Every header privacy arm funnels through :func:`_assert_free_of`, so the
    spelling set is widened THERE rather than in ten arms one at a time.
    """

    @dataclasses.dataclass
    class _CarriesARawSlice:
        """A parse result that carries a raw slice instead of stepping over it."""

        options_raw: bytes

    narrow = _CarriesARawSlice(MARKER_OPTIONS.encode("utf-8"))
    wide = _CarriesARawSlice(MARKER_OPTIONS.encode("utf-16-le"))

    # CONTROL - the sweep DOES catch the narrow spelling. Without this line a
    # blind oracle and a fixture that never held the needle look identical.
    with pytest.raises(AssertionError):
        _assert_free_of(_value_surfaces(narrow), (MARKER_OPTIONS,), "narrow control")

    # ISOLATION - the wide rendering carries no ASCII spelling of the marker,
    # and is itself pure ASCII, so no character-set gate stands in for this arm.
    rendered = repr(wide.options_raw)
    assert MARKER_OPTIONS not in rendered, "the wide rendering carries the ASCII spelling"
    assert rendered.isascii(), "an isascii gate would have caught this without the sweep"

    # THE CLAIM - the wide slice must leak just as loudly as the narrow one.
    with pytest.raises(AssertionError):
        _assert_free_of(_value_surfaces(wide), (MARKER_OPTIONS,), "wide raw slice")

    # FENCE - a result carrying NEITHER spelling still passes, so the widened
    # sweep has not become an assertion that fires on everything.
    clean = _CarriesARawSlice(b"nothing planted here")
    _assert_free_of(_value_surfaces(clean), (MARKER_OPTIONS,), "clean control")


def test_the_marker_selector_is_not_blind_to_a_wide_fixture() -> None:
    """PIECE 3 - THE NEEDLE SELECTOR KNEW EXACTLY ONE ENCODING. CS-964.

    :func:`_markers_present_in` decided presence by ``marker.encode("utf-8") in
    blob`` and ASSERTED the count it found, so a fixture whose fields are
    spliced to their wide spelling reddens it - two of the three markers go
    missing as far as it can tell. That is loud rather than silent, which makes
    it a signpost rather than a trap, but it still blocks every wide header arm
    at the first line.

    THE FIXTURE IS MIXED ON PURPOSE, which is why a single encoding parameter
    would be the wrong shape: ``_wide_marker_blob`` splices the options and
    session fields, the two a person types, and leaves the save name narrow. So
    presence is asked per marker across both spellings, and the plain text is
    still what comes back - :func:`_assert_free_of` now searches every spelling
    a renderer prints, so its callers keep handing it plain markers.
    """
    narrow = _markers_present_in(_marker_blob(VERSION_WITH_SAVE_NAME), VERSION_WITH_SAVE_NAME)
    assert narrow == MARKERS, "the narrow fixture no longer carries all three markers"

    # THE CLAIM - the same three markers are found in the mixed wide fixture.
    wide = _markers_present_in(_wide_marker_blob(), VERSION_WITH_SAVE_NAME)
    assert wide == MARKERS, (
        "the needle selector cannot see the wide-spelled markers, so every wide header "
        "arm reddens at its first line however correct its fixture is"
    )

    # FENCE - it still refuses a fixture that is genuinely missing a marker,
    # which is the vacuity check it was written for in the first place.
    stripped = _marker_blob(VERSION_WITH_SAVE_NAME).replace(
        synthetic.fstring(MARKER_SESSION), synthetic.fstring("HarmlessReplacement"), 1
    )
    with pytest.raises(AssertionError):
        _markers_present_in(stripped, VERSION_WITH_SAVE_NAME)


# ---------------------------------------------------------------------------
# Acceptance 1 - every dispatched fixture parses
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("save", synthetic.ALL_SAVES, ids=lambda save: save.name)
def test_every_dispatched_fixture_parses(save: synthetic.SyntheticSave) -> None:
    parsed = parse_header(save.blob)

    assert parsed.header_version == save.header_version
    assert parsed.save_version == save.save_version
    assert parsed.map_name == synthetic.MAP_NAME
    assert len(parsed.world_token) == TOKEN_LENGTH
    assert parsed.editor_object_version == EDITOR_OBJECT_VERSION


@pytest.mark.parametrize("save", synthetic.ALL_SAVES, ids=lambda save: save.name)
def test_the_world_token_is_the_fixtures_own_invented_token(
    save: synthetic.SyntheticSave,
) -> None:
    expected = (
        synthetic.SYNTHETIC_WORLD_TOKEN_B
        if save is synthetic.SAVE_CROSS
        else synthetic.SYNTHETIC_WORLD_TOKEN
    )

    assert parse_header(save.blob).world_token == expected


def test_two_saves_of_one_world_share_a_token_and_a_third_world_does_not() -> None:
    same = {parse_header(synthetic.SAVE_V52.blob).world_token}
    same.add(parse_header(synthetic.SAVE_V60.blob).world_token)

    assert len(same) == 1
    assert parse_header(synthetic.SAVE_CROSS.blob).world_token not in same


# ---------------------------------------------------------------------------
# Acceptance 2 - body_offset is the absolute offset of the chunk magic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("save", synthetic.ALL_SAVES, ids=lambda save: save.name)
def test_body_offset_lands_exactly_on_the_chunk_magic(save: synthetic.SyntheticSave) -> None:
    parsed = parse_header(save.blob)
    at = parsed.body_offset

    assert save.blob[at : at + 4] == struct.pack("<I", synthetic.CHUNK_MAGIC)


@pytest.mark.parametrize("save", synthetic.ALL_SAVES, ids=lambda save: save.name)
def test_body_offset_matches_the_corpus_chunk_offset(save: synthetic.SyntheticSave) -> None:
    assert parse_header(save.blob).body_offset == save.chunk_offset


def test_the_header_tail_is_present_on_13_and_14_and_absent_on_10() -> None:
    without_tail = parse_header(synthetic.SAVE_V36.blob).body_offset
    with_tail = parse_header(synthetic.SAVE_V42.blob).body_offset

    # SAVE_V36 is header 10 and SAVE_V42 is header 13. Both carry three
    # strings, so the whole difference between their header lengths is the
    # 28-byte tail plus the identical fixed block.
    assert with_tail - without_tail == synthetic.HEADER_TAIL_SIZE


# ---------------------------------------------------------------------------
# Acceptance 3 - string layout follows the HEADER version, not the save version
# ---------------------------------------------------------------------------


def test_string_layout_follows_the_header_version_not_the_save_version() -> None:
    """SAVE_CROSS is header 14 with save 36 - a pair that occurs in no real file.

    A parser keying the string block off ``save_version`` reads three strings
    instead of four, so ``map_name`` receives the SAVE NAME and the cursor
    stops 28 + 22 bytes short of the magic. Both halves are asserted, because
    either one alone can be satisfied by a different bug.
    """
    cross = synthetic.SAVE_CROSS
    parsed = parse_header(cross.blob)

    assert parsed.header_version == HEADER_14
    assert parsed.save_version == CROSS_SAVE_VERSION
    assert parsed.map_name == synthetic.MAP_NAME
    assert parsed.map_name != synthetic.SYNTHETIC_SAVE_NAME
    assert parsed.body_offset == cross.chunk_offset


def test_header_10_reads_three_strings_and_lands_on_the_magic() -> None:
    """The mirror of the case above - the older layout, which has no save name."""
    save = synthetic.SAVE_V36
    parsed = parse_header(save.blob)
    at = parsed.body_offset

    assert parsed.header_version == HEADER_10
    assert parsed.map_name == synthetic.MAP_NAME
    assert save.blob[at : at + 4] == struct.pack("<I", synthetic.CHUNK_MAGIC)


def test_an_unmeasured_version_pair_is_flagged_rather_than_refused() -> None:
    """Non-negotiable 7 and ADR 0007 decision item 3: flag and continue, never fatal."""
    cross = parse_header(synthetic.SAVE_CROSS.blob)
    measured = parse_header(synthetic.SAVE_V60.blob)

    assert any(
        warning.code == header_module.WARN_UNMEASURED_VERSION_PAIR for warning in cross.warnings
    )
    assert measured.warnings == ()


# ---------------------------------------------------------------------------
# Acceptance 4 - every corruption fixture raises its specified type
# ---------------------------------------------------------------------------

#: The file-scope cut points that land INSIDE the header, or inside the four
#: magic bytes the header's own seam promise covers. Derived from the corpus
#: rather than restated, so a change to the fixture cannot silently drop a case.
_HEADER_SCOPE_CUTS: Final = tuple(
    point
    for point in synthetic.TRUNCATION_BOUNDARIES
    if point.scope == synthetic.SCOPE_FILE and point.offset < synthetic.SAVE_V60.chunk_offset + 4
)

#: The file-scope cut points that land beyond the magic, entirely inside the
#: chunk frame. The header is complete and correct at each, and chunks.py owns
#: the damage. See the module docstring.
_CHUNK_SCOPE_CUTS: Final = tuple(
    point
    for point in synthetic.TRUNCATION_BOUNDARIES
    if point.scope == synthetic.SCOPE_FILE and point.offset >= synthetic.SAVE_V60.chunk_offset + 4
)


def test_the_truncation_matrix_is_fully_partitioned() -> None:
    """Every file-scope boundary is claimed by exactly one of the two lists above.

    Without this, a cut point added to the corpus later would silently fall
    through both filters and be asserted by nothing.
    """
    file_scope = [
        point for point in synthetic.TRUNCATION_BOUNDARIES if point.scope == synthetic.SCOPE_FILE
    ]

    assert len(_HEADER_SCOPE_CUTS) + len(_CHUNK_SCOPE_CUTS) == len(file_scope)
    assert _HEADER_SCOPE_CUTS
    assert _CHUNK_SCOPE_CUTS


@pytest.mark.parametrize("point", _HEADER_SCOPE_CUTS, ids=lambda point: point.label)
def test_truncation_inside_the_header_raises_truncated(
    point: synthetic.TruncationPoint,
) -> None:
    blob = synthetic.truncated_at(synthetic.SAVE_V60.blob, point.offset)

    with pytest.raises(HeaderTruncatedError):
        parse_header(blob)


@pytest.mark.parametrize("point", _CHUNK_SCOPE_CUTS, ids=lambda point: point.label)
def test_truncation_beyond_the_magic_leaves_the_header_intact(
    point: synthetic.TruncationPoint,
) -> None:
    """The header is complete at these cuts, so it parses and reports the magic.

    Asserting the SUCCESS is the point. A header parser that raised here would
    be validating the chunk frame, which is the neighbouring module's job.
    """
    blob = synthetic.truncated_at(synthetic.SAVE_V60.blob, point.offset)

    parsed = parse_header(blob)
    at = parsed.body_offset

    assert parsed.body_offset == synthetic.SAVE_V60.chunk_offset
    assert blob[at : at + 4] == struct.pack("<I", synthetic.CHUNK_MAGIC)


def test_every_truncation_of_the_header_region_raises_or_parses_cleanly() -> None:
    """Cut at EVERY byte offset in the header region - no offset may crash oddly.

    The named boundaries above are the interesting cuts. This is the sweep that
    catches the offset nobody thought to name, and it asserts the failure is
    always one of this module's own types rather than a struct error, an index
    error or a UnicodeDecodeError carrying raw bytes.
    """
    save = synthetic.SAVE_V60
    limit = save.chunk_offset + 4

    for cut in range(limit + 1):
        blob = synthetic.truncated_at(save.blob, cut)
        if cut == limit:
            assert parse_header(blob).body_offset == save.chunk_offset
            continue
        with pytest.raises(HeaderError) as caught:
            parse_header(blob)
        assert isinstance(caught.value, HeaderTruncatedError), (
            f"cut at {cut} raised {type(caught.value).__name__}, expected a truncation"
        )


def test_absurd_string_length_is_refused_before_allocating() -> None:
    """A declared 2**30-byte string in a 384-byte file is refused on the DECLARATION.

    The cap is checked before the remaining length is consulted and before any
    slice is taken, which is what "bound before you allocate" means. That is
    also why this is a FORMAT error and not a truncation: the file declares
    something structurally impossible rather than merely being short.
    """
    with pytest.raises(HeaderFormatError) as caught:
        parse_header(synthetic.absurd_string_length())

    assert caught.value.declared == synthetic.ABSURD_STRING_LENGTH


def test_negative_string_length_is_refused_before_allocating() -> None:
    """The negative sign selects UTF-16, so the magnitude is doubled before the cap."""
    with pytest.raises(HeaderFormatError) as caught:
        parse_header(synthetic.negative_string_length())

    assert caught.value.declared == -synthetic.NEGATIVE_STRING_LENGTH * 2


def test_a_string_length_under_the_cap_but_over_the_file_is_a_truncation() -> None:
    """The sibling case that separates the two error types.

    Without this, a parser could pass both tests above by calling every
    over-long string a format error, and the distinction between "declares
    nonsense" and "file is short" would be untested.
    """
    over_the_file = 4096
    assert over_the_file < header_module.MAX_STRING_BYTES

    blob = (
        synthetic.SAVE_V60.blob[:FIRST_STRING_COUNT_OFFSET]
        + struct.pack("<i", over_the_file)
        + synthetic.SAVE_V60.blob[FIRST_STRING_COUNT_OFFSET + 4 :]
    )

    with pytest.raises(HeaderTruncatedError):
        parse_header(blob)


def test_unsupported_header_version_is_refused_on_the_version() -> None:
    """The fixture is structurally well formed, so only the version can reject it."""
    with pytest.raises(UnsupportedHeaderVersionError) as caught:
        parse_header(synthetic.unsupported_header_version())

    assert caught.value.header_version == synthetic.UNSUPPORTED_HEADER_VERSION


def test_the_version_check_happens_before_any_string_is_read() -> None:
    """Ordering matters: a version check after the string block never fires.

    A header declaring version 99 with a truncated string block must still be
    rejected on the VERSION, because the layout for 99 is unknown and reading
    it is exactly the guess ADR 0007 forbids.
    """
    blob = synthetic.truncated_at(synthetic.unsupported_header_version(), 14)

    with pytest.raises(UnsupportedHeaderVersionError):
        parse_header(blob)


def test_an_empty_input_is_a_truncation_rather_than_an_index_error() -> None:
    with pytest.raises(HeaderTruncatedError):
        parse_header(b"")


# ---------------------------------------------------------------------------
# Acceptance 5 - the planted-marker test
# ---------------------------------------------------------------------------


#: The two header fields the wide drive respells, and the reason it is these
#: two: they are the ones a PERSON TYPES, so they are the ones that carry a
#: non-ASCII character on a real save and therefore arrive UTF-16-LE with a
#: negative count. The save name is deliberately left narrow, which is what
#: makes the wide fixture MIXED - see `_markers_present_in`.
WIDE_SPLICED_FIELDS: Final = ("?" + MARKER_OPTIONS + "=1", MARKER_SESSION)


def _respell(data: bytes, spelling: str) -> bytes:
    """``data`` with the personal-data fields in the requested spelling.

    Args:
        data: A marker-bearing header or whole save, built by the narrow path
            like every other fixture in this module.
        spelling: ``"narrow"`` to leave it alone, ``"wide"`` to respell.

    Returns:
        The bytes, respelled or untouched.
    """
    if spelling == "narrow":
        return data
    return test_properties._spliced_wide(data, *WIDE_SPLICED_FIELDS)  # noqa: SLF001


def _marker_header_length_at(header_version: int, spelling: str) -> int:
    """The marker header's byte length AT THIS SPELLING.

    The wide fields are longer, so a truncation loop bounded by the narrow
    length stops short of the wide string block and never enters the frames the
    arm is about. Deriving the bound per spelling is what keeps that arm from
    being vacuous.

    Args:
        header_version: 10, 13 or 14.
        spelling: ``"narrow"`` or ``"wide"``.

    Returns:
        The byte length of the header alone, respelled.
    """
    kwargs = _marker_header_kwargs(header_version)
    return len(_respell(synthetic.build_header(**kwargs), spelling))  # type: ignore[arg-type]


@pytest.mark.parametrize("header_version", HEADER_VERSIONS)
@pytest.mark.parametrize("spelling", ["narrow", "wide"])
def test_planted_markers_never_reach_any_surface(header_version: int, spelling: str) -> None:
    """The load-bearing test. See the module docstring.

    Drives the success path and every failure path this module has, at every
    header version AND AT BOTH ON-WIRE ENCODINGS, and asserts the planted
    markers reach none of the surfaces a human or a log can read.

    WHY BOTH SPELLINGS (CS-964). Unreal writes a string UTF-16-LE with a
    negative count the moment it carries one non-ASCII character, which the
    session name and the player display name - the two a person types - readily
    do. This arm drove the narrow spelling only, so its whole population of
    green verdicts was measured against the encoding those fields are LEAST
    likely to have. An adversary then measured the consequence rather than
    arguing it: a parse result carrying a raw slice - the exact regression this
    arm exists to catch, since the design is that the bytes never become Python
    strings at all - DIES against the narrow field and SURVIVES against the
    wide one.

    THE WIDE FIXTURE IS SPLICED, NOT SEPARATELY BUILT. One builder, one blob,
    two spellings: a parallel wide builder is a fixture that can drift away
    from the narrow one, and the drift would be invisible because both parse.
    The splice asserts it landed; a second builder could not.

    EVERY DERIVED OFFSET IS RE-DERIVED PER SPELLING. The wide fields are longer,
    so the header length is taken from the respelled header rather than the
    narrow one - a truncation loop bounded by the narrow length would stop short
    of the wide string block and never reach the frames this arm is about.
    """
    narrow = _marker_blob(header_version)
    blob = _respell(narrow, spelling)

    # CS-964 - THE WIDE DRIVE'S WIDENESS IS ASSERTED, NOT ASSUMED, and this
    # check exists because an adversary measured its absence. Reducing
    # `_respell` to `return data` - so the "wide" ids become byte-identical
    # duplicates of the narrow ones - left the whole of `tests/save` GREEN at
    # 1511 passed. Nothing anywhere noticed that the wide half of a
    # parametrization named for its encoding was not wide. The splice helper
    # has its own arm, but the ARM'S USE of it had none, which is the same
    # defect one level out: a fixture property that decides what a whole
    # parametrized population measures, graded by nothing.
    if spelling == "wide":
        assert blob != narrow, (
            "the wide spelling is byte-identical to the narrow one, so this half of the "
            "parametrization is a duplicate of the other half and measures nothing"
        )
        assert MARKER_SESSION.encode("utf-16-le") in blob, (
            "the respelled blob does not carry the session marker in its wide spelling"
        )
        assert MARKER_SESSION.encode("utf-8") not in blob, (
            "the respelled blob still carries the session marker NARROW, so the splice "
            "left the encoding this arm was written to stop measuring"
        )

    needles = _markers_present_in(blob, header_version)

    # THE CONTROL THE ACCEPTANCE CLAUSE REQUIRES, per needle: the sweep can
    # SEE this value in the spelling THIS fixture carries. Without it, a wide
    # drive whose needles were still narrow would report clean for the one
    # reason that proves nothing - and that is the trap this item is named for.
    for marker in needles:
        found = _spelling_of(marker, blob)
        assert found is not None, f"{marker!r} is in neither spelling, so its sweep is vacuous"
        test_properties._assert_the_needle_is_observable(marker, found)  # noqa: SLF001

    # --- the success path -------------------------------------------------
    parsed = parse_header(blob)
    _assert_free_of(_value_surfaces(parsed), needles, f"SaveHeader success path ({spelling})")
    _assert_free_of([repr(parsed.warnings)], needles, f"warnings ({spelling})")

    # --- truncation, at every offset in the header region ------------------
    header_length = _marker_header_length_at(header_version, spelling)
    for cut in range(header_length + 4):
        try:
            parse_header(synthetic.truncated_at(blob, cut))
        except HeaderError as error:
            _assert_free_of(
                _exception_surfaces(error), needles, f"truncation at {cut} ({spelling})"
            )

    # --- a declared length above the cap -----------------------------------
    # The splice lands AFTER this offset at every header version - asserted,
    # not assumed, because a respelling that moved it would make the cap path
    # test a different field than the one it names.
    assert (
        blob[:FIRST_STRING_COUNT_OFFSET] == _marker_blob(header_version)[:FIRST_STRING_COUNT_OFFSET]
    ), "the respelling moved the first string's count field, so the cap path below has drifted"
    absurd = (
        blob[:FIRST_STRING_COUNT_OFFSET]
        + struct.pack("<i", synthetic.ABSURD_STRING_LENGTH)
        + blob[FIRST_STRING_COUNT_OFFSET + 4 :]
    )
    with pytest.raises(HeaderFormatError) as format_error:
        parse_header(absurd)
    _assert_free_of(
        _exception_surfaces(format_error.value), needles, f"declared length above cap ({spelling})"
    )

    # --- an unsupported version, with the markers still in the bytes -------
    kwargs = _marker_header_kwargs(header_version)
    kwargs["header_version"] = synthetic.UNSUPPORTED_HEADER_VERSION
    kwargs["with_save_name"] = True
    kwargs["with_tail"] = True
    unsupported = _respell(synthetic.build_save(header_kwargs=kwargs), spelling)
    with pytest.raises(UnsupportedHeaderVersionError) as version_error:
        parse_header(unsupported)
    _assert_free_of(
        _exception_surfaces(version_error.value), needles, f"unsupported version ({spelling})"
    )

    # --- the opt-in refusal ------------------------------------------------
    with pytest.raises(PersonalDataOptInRequiredError) as opt_in_error:
        reveal_strings(blob)
    _assert_free_of(
        _exception_surfaces(opt_in_error.value), needles, f"opt-in refusal ({spelling})"
    )

    # --- the withheld repr of the opt-in RESULT ----------------------------
    revealed = reveal_strings(blob, reveal_personal_data=True)
    _assert_free_of([repr(revealed), str(revealed)], needles, f"HeaderStrings repr ({spelling})")


def test_the_marker_fixture_really_does_carry_the_markers() -> None:
    """The control. Without it every assertion above could pass vacuously.

    If the builder stopped emitting the strings, or the markers were misspelled
    at one site, every "marker not found" assertion would succeed against bytes
    that never held a marker.
    """
    for header_version in HEADER_VERSIONS:
        blob = _marker_blob(header_version)
        expected = len(MARKERS) if header_version >= VERSION_WITH_SAVE_NAME else len(MARKERS) - 1
        found = [marker for marker in MARKERS if marker.encode("utf-8") in blob]

        assert len(found) == expected
        assert MARKER_OPTIONS.encode("utf-8") in blob
        assert MARKER_SESSION.encode("utf-8") in blob


@pytest.mark.parametrize("header_version", HEADER_VERSIONS)
def test_the_repr_carries_versions_and_a_masked_token_only(header_version: int) -> None:
    """The generated repr prints every field, and pytest reprs objects into the log."""
    parsed = parse_header(_marker_blob(header_version))
    rendered = repr(parsed)

    assert str(header_version) in rendered
    assert parsed.world_token not in rendered
    assert masked_token(parsed.world_token) in rendered
    assert synthetic.MAP_NAME not in rendered


def test_masked_token_discloses_no_character_of_the_token() -> None:
    # The mask is a digest rather than a head-and-tail reveal, so NO run of the
    # real token survives into the rendering. A head-and-tail mask would leak
    # real characters of real personal data into every repr that renders one.
    token = synthetic.SYNTHETIC_WORLD_TOKEN
    masked = masked_token(token)

    assert masked != token
    assert token not in masked
    # No substring of the token of length 3 or more appears in the rendering.
    # Length 3 rather than 1 because single characters collide with hex by
    # chance and would make this assertion about nothing.
    runs = {token[i : i + 3] for i in range(len(token) - 2)}
    assert not any(run in masked for run in runs)


def test_masked_token_is_stable_and_distinguishes_two_worlds() -> None:
    # This is the ONLY property a debug line actually needs: same world reads
    # the same, different worlds read differently.
    a = synthetic.SYNTHETIC_WORLD_TOKEN
    b = synthetic.SYNTHETIC_WORLD_TOKEN_B

    assert masked_token(a) == masked_token(a)
    assert masked_token(a) != masked_token(b)


def test_masked_token_renders_an_empty_token_as_the_prefix_alone() -> None:
    # An empty value has nothing to correlate, so it gets no digest.
    assert masked_token("") == header_module.MASK_PREFIX


# ---------------------------------------------------------------------------
# The default parse must not DECODE the personal-data strings at all
# ---------------------------------------------------------------------------
#
# Absent from the returned type is the first guarantee. Never becoming a Python
# string in the first place is the second, and it is the one that covers a
# local-variable dump, a debugger frame and a chained exception context. Two
# independent checks below, because each catches what the other cannot: the
# functional one proves the behaviour on real bytes, and the structural one
# proves it for every input rather than for the one that was tried.

#: A distinctive ASCII run planted in a header string so a byte inside it can
#: be found and corrupted without changing any length.
UNDECODABLE_PROBE: Final = "SessionPayloadProbe"


def _blob_with_an_undecodable_session_name() -> bytes:
    """Build a save whose session name contains a byte that is not valid UTF-8.

    Returns:
        The blob, the same length as the undamaged one.
    """
    blob = synthetic.build_save(
        header_kwargs={
            "header_version": 14,
            "save_version": 60,
            "session_name": UNDECODABLE_PROBE,
        }
    )
    needle = UNDECODABLE_PROBE.encode("utf-8")
    assert blob.count(needle) == 1
    return blob.replace(needle, b"\xff" + needle[1:], 1)


def test_the_default_parse_never_decodes_the_personal_data_strings() -> None:
    """The functional half. 0xFF is not valid UTF-8 anywhere.

    A parser that decoded the session name would raise on these bytes. One
    that steps over them by length cannot even notice, which is the point -
    the value never becomes a Python string, so there is nothing for a locals
    dump or an exception context to carry.
    """
    blob = _blob_with_an_undecodable_session_name()

    parsed = parse_header(blob)

    assert parsed.map_name == synthetic.MAP_NAME
    assert parsed.world_token == synthetic.SYNTHETIC_WORLD_TOKEN


def test_the_opt_in_path_does_decode_and_therefore_does_reject_bad_bytes() -> None:
    """The control for the test above.

    Without it, a parser that silently produced mojibake would pass the
    functional check while genuinely decoding. This proves the bytes really
    are undecodable, so the success above is the skip and not a lenient decode.
    """
    blob = _blob_with_an_undecodable_session_name()

    with pytest.raises(HeaderFormatError) as caught:
        reveal_strings(blob, reveal_personal_data=True)

    assert caught.value.reason == header_module.REASON_UNDECODABLE_TEXT


def _string_calls_in(function_name: str) -> tuple[int, int]:
    """Count decode calls and skip calls inside one parser function, from its AST.

    Args:
        function_name: The function to inspect.

    Returns:
        ``(cursor.string calls, cursor.skip_string calls)``.
    """
    source = Path(header_module.__file__ or "").read_text(encoding="utf-8")
    target = next(
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    )
    decoded = 0
    skipped = 0
    for node in ast.walk(target):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "string":
                decoded += 1
            elif node.func.attr == "skip_string":
                skipped += 1
    return decoded, skipped


def test_parse_header_decodes_only_the_two_non_personal_strings() -> None:
    """The structural half, and it holds for every input rather than one fixture.

    Exactly two strings may be decoded on the default path - the map name,
    which is a fixed game constant, and the identifier. The other four slots -
    save name, options, session name and mod metadata - are stepped over.
    """
    decoded, skipped = _string_calls_in("parse_header")

    assert decoded == DECODED_IN_PARSE, "parse_header decodes a string it may not decode"
    assert skipped == SKIPPED_IN_PARSE


def test_reveal_strings_is_the_only_function_that_decodes_them() -> None:
    """The opt-in path is the sole decoder, which is what makes it the sole leak site."""
    decoded, skipped = _string_calls_in("reveal_strings")

    assert decoded == DECODED_IN_REVEAL
    assert skipped == 0


# ---------------------------------------------------------------------------
# Acceptance 6 - no SaveHeader field holds a personal-data string
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("save", synthetic.ALL_SAVES, ids=lambda save: save.name)
def test_no_save_header_field_holds_a_personal_data_string(
    save: synthetic.SyntheticSave,
) -> None:
    """Enumerate the dataclass fields and assert none carries one of the three.

    Unreachable beats redacted. ADR 0007 decision item 4 puts the PII-bearing
    strings off the returned type entirely, so this test is the mechanical
    statement of that decision.
    """
    forbidden = (
        synthetic.SYNTHETIC_SAVE_NAME,
        synthetic.SYNTHETIC_OPTIONS,
        synthetic.SYNTHETIC_SESSION_NAME,
    )
    parsed = parse_header(save.blob)

    for entry in dataclasses.fields(parsed):
        value = getattr(parsed, entry.name)
        for needle in forbidden:
            assert needle not in str(value), f"{entry.name} carries a personal-data string"
            assert needle not in repr(value), f"{entry.name} carries a personal-data string"


def test_save_header_declares_no_field_named_for_a_personal_data_string() -> None:
    """A name check as well as a value check.

    A field called ``session_name`` that happens to be empty on the corpus
    would pass the value test above and would still be the design ADR 0007
    forbids.
    """
    names = {entry.name for entry in dataclasses.fields(SaveHeader)}

    assert not names & {"save_name", "options", "map_options", "session_name", "world_name"}


def test_the_unverified_int8_is_named_for_its_position_not_a_meaning() -> None:
    """ADR 0007 decision item 5. It reads 0x10, 0x50, 0x90 or 0xD0 on 8 of 14 real saves.

    A parser calling it "session visibility" is asserting a flag, and is wrong
    on the majority of the operator's own header-14 files.
    """
    names = {entry.name for entry in dataclasses.fields(SaveHeader)}

    assert "byte_after_datetime_ticks" in names
    assert not any("visib" in name for name in names)


# ---------------------------------------------------------------------------
# Acceptance 7 - the opt-in path
# ---------------------------------------------------------------------------


def test_reveal_strings_without_the_opt_in_raises() -> None:
    with pytest.raises(PersonalDataOptInRequiredError):
        reveal_strings(synthetic.SAVE_V60.blob)


def test_reveal_strings_with_the_opt_in_returns_the_real_values() -> None:
    revealed = reveal_strings(synthetic.SAVE_V60.blob, reveal_personal_data=True)

    assert revealed.save_name == synthetic.SYNTHETIC_SAVE_NAME
    assert revealed.map_name == synthetic.MAP_NAME
    assert revealed.map_options == synthetic.SYNTHETIC_OPTIONS
    assert revealed.session_name == synthetic.SYNTHETIC_SESSION_NAME


def test_reveal_strings_on_header_10_returns_no_save_name() -> None:
    """The older layout has three strings, and the absent one is reported as None."""
    revealed = reveal_strings(synthetic.SAVE_V36.blob, reveal_personal_data=True)

    assert revealed.save_name is None
    assert revealed.map_name == synthetic.MAP_NAME
    assert revealed.map_options == synthetic.SYNTHETIC_OPTIONS
    assert revealed.session_name == synthetic.SYNTHETIC_SESSION_NAME


def test_the_opt_in_is_keyword_only_so_it_cannot_be_passed_by_accident() -> None:
    signature = inspect.signature(reveal_strings)
    parameter = signature.parameters["reveal_personal_data"]

    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is False

    # Routed through an untyped alias so the call is a RUNTIME test of the
    # keyword-only signature rather than a type-checker suppression.
    loose: Any = reveal_strings
    with pytest.raises(TypeError):
        loose(synthetic.SAVE_V60.blob, True)


def test_header_strings_withholds_its_own_repr() -> None:
    """The opt-in result is render-site only, and pytest reprs objects into the log."""
    revealed = reveal_strings(synthetic.SAVE_V60.blob, reveal_personal_data=True)

    assert synthetic.SYNTHETIC_SESSION_NAME not in repr(revealed)
    assert synthetic.SYNTHETIC_OPTIONS not in repr(revealed)
    assert HeaderStrings.__name__ in repr(revealed)


def test_reveal_strings_still_refuses_an_unsupported_version() -> None:
    """The opt-in is not a bypass for the version dispatch."""
    with pytest.raises(UnsupportedHeaderVersionError):
        reveal_strings(synthetic.unsupported_header_version(), reveal_personal_data=True)


# ---------------------------------------------------------------------------
# The error taxonomy, enforced statically
# ---------------------------------------------------------------------------

#: The complete vocabulary of parameter names any error in this module may
#: take: a field NAME, a byte OFFSET, an expected/actual LENGTH or COUNT, a
#: version scalar, a fixed reason, an already-redacted path, and an errno.
_ALLOWED_ERROR_PARAMETERS: Final = frozenset(
    {
        "field",
        "offset",
        "needed",
        "available",
        "declared",
        "limit",
        "reason",
        "header_version",
        "redacted_path",
        "errno",
    }
)

_ALLOWED_ERROR_ANNOTATIONS: Final = frozenset({"str", "int", "int | None"})


def _error_classes() -> list[type[HeaderError]]:
    """Every error class this module defines.

    Returns:
        The classes, base included.
    """
    return [
        value
        for value in vars(header_module).values()
        if isinstance(value, type) and issubclass(value, HeaderError)
    ]


def test_the_error_hierarchy_is_the_declared_one() -> None:
    found = {cls.__name__ for cls in _error_classes()}

    assert found == {
        "HeaderError",
        "HeaderTruncatedError",
        "HeaderFormatError",
        "HeaderReadError",
        "UnsupportedHeaderVersionError",
        "PersonalDataOptInRequiredError",
    }
    for cls in _error_classes():
        assert issubclass(cls, Exception)


def test_every_error_class_takes_only_taxonomy_safe_parameters() -> None:
    """The static gate. No PARAMETER exists through which content could travel.

    A sampled test proves only the raise sites it reached. This proves the
    surface, so a raise site written next month is covered too.
    """
    for cls in _error_classes():
        if cls is HeaderError:
            continue
        assert "__init__" in vars(cls), (
            f"{cls.__name__} inherits Exception's *args, which accepts anything"
        )
        signature = inspect.signature(cls.__init__)
        for name, parameter in signature.parameters.items():
            if name == "self":
                continue
            assert parameter.kind not in {
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            }, f"{cls.__name__} accepts *args or **kwargs"
            assert name in _ALLOWED_ERROR_PARAMETERS, (
                f"{cls.__name__} takes a parameter outside the taxonomy: {name}"
            )
            annotation = parameter.annotation
            if isinstance(annotation, str):
                rendered = annotation
            else:
                rendered = getattr(annotation, "__name__", str(annotation))
            assert rendered in _ALLOWED_ERROR_ANNOTATIONS, (
                f"{cls.__name__}.{name} is annotated {rendered}, outside the taxonomy"
            )


def test_a_field_name_outside_the_vocabulary_is_refused() -> None:
    """The runtime half of the gate.

    The static gate proves the parameter is a str. This proves the str is
    drawn from a closed vocabulary, so a raise site cannot smuggle content
    through the one parameter that is allowed to be text.
    """
    with pytest.raises(ValueError, match="field name"):
        HeaderTruncatedError(field="a decoded world name", offset=0, needed=1, available=0)


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param(lambda: parse_header(b""), id="truncated"),
        pytest.param(lambda: parse_header(synthetic.absurd_string_length()), id="format"),
        pytest.param(lambda: parse_header(synthetic.unsupported_header_version()), id="version"),
        pytest.param(lambda: reveal_strings(synthetic.SAVE_V60.blob), id="opt-in"),
    ],
)
def test_no_error_message_looks_like_a_byte_dump(factory: Callable[[], object]) -> None:
    """No raised message may carry an escape sequence, a bytes literal or a hex preview."""
    with pytest.raises(HeaderError) as caught:
        factory()

    for surface in [str(caught.value), repr(caught.value.args)]:
        assert "\\x" not in surface
        assert "b'" not in surface
        assert 'b"' not in surface
        assert "0x" not in surface


def test_the_unsupported_version_error_names_the_integer_and_nothing_else() -> None:
    declared = synthetic.UNSUPPORTED_HEADER_VERSION
    error = UnsupportedHeaderVersionError(declared)

    assert error.header_version == declared
    assert str(declared) in str(error)
    assert error.args == (str(error),)


# ---------------------------------------------------------------------------
# read_header - the bounded, path-redacting entry point
# ---------------------------------------------------------------------------


def test_read_header_parses_a_file_written_from_the_corpus(tmp_path: Path) -> None:
    """The one place this module touches a filesystem, and it writes only a synthetic blob."""
    target = tmp_path / "synthetic_fixture.bin"
    target.write_bytes(synthetic.SAVE_V60.blob)

    parsed = read_header(target)

    assert parsed.body_offset == synthetic.SAVE_V60.chunk_offset
    token_is_the_fixture_token = parsed.world_token == synthetic.SYNTHETIC_WORLD_TOKEN
    assert token_is_the_fixture_token, "the header's world token is not the fixture's"


def test_read_header_redacts_the_path_of_a_file_it_cannot_open(tmp_path: Path) -> None:
    """A save filename embeds the world name, so an OSError message is a leak path.

    The stem below stands in for an operator-chosen world name. It must not
    survive into the message, the args or the traceback.
    """
    missing = tmp_path / "PlantedWorldNameNeedle.sav"

    with pytest.raises(HeaderReadError) as caught:
        read_header(missing)

    for surface in _exception_surfaces(caught.value):
        assert "PlantedWorldNameNeedle" not in surface
    assert "<save-file>" in str(caught.value)


def test_read_header_does_not_leak_the_original_oserror_as_context(tmp_path: Path) -> None:
    """``raise ... from None`` matters here.

    Without it the implicit ``__context__`` is set and the formatted traceback
    prints the original FileNotFoundError, filename and all - so the redaction
    above would be defeated by the very next line of the same traceback.
    """
    missing = tmp_path / "PlantedWorldNameNeedle.sav"

    with pytest.raises(HeaderReadError) as caught:
        read_header(missing)

    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None or caught.value.__suppress_context__


def test_read_header_reads_a_bounded_prefix_rather_than_the_whole_file(
    tmp_path: Path,
) -> None:
    """A save is untrusted binary input and is measured in megabytes.

    The file below is padded far past the cap. The parse must still succeed and
    must still report the same body offset, which is only possible if the read
    is bounded and the offset is absolute.
    """
    target = tmp_path / "padded_fixture.bin"
    padding = bytes(header_module.MAX_HEADER_BYTES * 2)
    target.write_bytes(synthetic.SAVE_V60.blob + padding)

    parsed = read_header(target)

    assert parsed.body_offset == synthetic.SAVE_V60.chunk_offset


# ---------------------------------------------------------------------------
# Warnings
# ---------------------------------------------------------------------------


def test_a_warning_carries_no_decoded_content() -> None:
    """Warnings are an echo path too (non-negotiable 12)."""
    parsed = parse_header(synthetic.SAVE_CROSS.blob)

    assert parsed.warnings
    for warning in parsed.warnings:
        assert isinstance(warning, HeaderWarning)
        assert synthetic.SYNTHETIC_SESSION_NAME not in repr(warning)
        assert synthetic.SYNTHETIC_OPTIONS not in repr(warning)
        assert parsed.world_token not in repr(warning)


def test_warnings_are_a_tuple_so_a_caller_cannot_mutate_the_record() -> None:
    assert isinstance(parse_header(synthetic.SAVE_V60.blob).warnings, tuple)


def test_the_parser_does_not_import_the_fixture_builder() -> None:
    """Independence is the whole reason the two spell the constants separately.

    If the parser imported the builder, every offset assertion in this module
    would be the builder agreeing with itself rather than a check on it.
    """
    source = Path(header_module.__file__ or "").read_text(encoding="utf-8")

    assert "import synthetic" not in source
    assert "from tests" not in source
    assert "tests.save" not in source
    assert "import tests" not in source


# ---------------------------------------------------------------------------
# CS-963 - the frames that hold the raw save across a refusal
# ---------------------------------------------------------------------------


def _cut_inside_the_session_name(header_version: int) -> bytes:
    """A marker blob cut mid-way through its LAST header string.

    Cutting there is what keeps the arms below non-vacuous: the options marker
    is fully encoded before the cut, so the bytes handed to the parser really do
    carry the plaintext string whose absence from every frame is the claim.

    Args:
        header_version: 10, 13 or 14.

    Returns:
        The truncated blob.
    """
    blob = _marker_blob(header_version)
    at = blob.index(MARKER_SESSION.encode("utf-8"))
    cut = blob[: at + 2]
    assert MARKER_OPTIONS.encode("utf-8") in cut, (
        "the cut removed the options marker, so any sweep over it would be vacuous"
    )
    return cut


def test_reveal_strings_leaves_no_frame_holding_the_raw_save_when_it_refuses() -> None:
    """CS-963 at the OPT-IN path, which the first repair left unguarded.

    ``reveal_strings`` is the one function in this module that returns the
    personal-data strings on purpose, and that makes it the easiest place to
    assume the question has already been answered. It has not been: its ``data``
    parameter is the whole save, and a refusal mid-string block unwinds through
    its frame with the options string still bound (non-negotiable 12).

    MEASURED BY MUTATION rather than asserted: with this arm absent, removing
    the scrub from ``reveal_strings`` left the whole save-layer suite green.
    """
    cut = _cut_inside_the_session_name(VERSION_WITH_SAVE_NAME)

    # CONTROL: the oracle can see the marker in the bytes that hold it, so an
    # empty verdict below is a measurement and not the oracle's own blindness.
    assert MARKER_OPTIONS in test_properties._safe_repr(cut)  # noqa: SLF001

    with pytest.raises(HeaderError) as caught:
        header_module.reveal_strings(cut, reveal_personal_data=True)
    raised = caught.value

    entered = test_properties._shipped_frame_names(raised)  # noqa: SLF001
    assert "reveal_strings" in entered, (
        f"the refusal never entered reveal_strings, so nothing was swept. Reached: {entered}"
    )

    leaks = test_properties._shipped_frames(raised, MARKER_OPTIONS)  # noqa: SLF001
    assert not leaks, (
        "reveal_strings leaves the raw save in a frame a locals-showing renderer prints, "
        f"options string and all (non-negotiable 12). Offending: {leaks}"
    )


def test_read_header_leaves_no_frame_holding_the_prefix_when_it_refuses(tmp_path: Path) -> None:
    """CS-963 at the PATH entry point, and its bound prefix is the worst case.

    ``read_header`` reads only ``MAX_HEADER_BYTES`` - which is not a mitigation
    here but the opposite. The bounded prefix is PRECISELY the plaintext string
    region; nothing else is in it. A refusal out of ``parse_header`` unwinds
    through this frame, so scrubbing the callee alone repaired one of two.

    Driven through a real file on disk rather than by calling ``parse_header``,
    because the frame under test only exists on the path entry.
    """
    cut = _cut_inside_the_session_name(VERSION_WITH_SAVE_NAME)
    source = tmp_path / "cs963-read-header.sav"
    source.write_bytes(cut)

    with pytest.raises(HeaderError) as caught:
        header_module.read_header(source)
    raised = caught.value

    entered = test_properties._shipped_frame_names(raised)  # noqa: SLF001
    assert "read_header" in entered, (
        f"the refusal never entered read_header, so nothing was swept. Reached: {entered}"
    )

    leaks = test_properties._shipped_frames(raised, MARKER_OPTIONS)  # noqa: SLF001
    assert not leaks, (
        "read_header leaves its bounded prefix - the plaintext string region itself - in "
        f"a frame a renderer prints (non-negotiable 12). Offending: {leaks}"
    )


def _wide_marker_blob() -> bytes:
    """A marker blob whose options and session strings are UTF-16-LE.

    `synthetic.build_header` writes every string as UTF-8 with a positive count,
    which is what a save carries only while every character is ASCII. Unreal
    writes UTF-16-LE with a NEGATIVE count the moment one is not - and the
    fields that carry personal data are exactly the ones a person types. So the
    two fields are SPLICED to their wide spelling rather than a second header
    builder being written: the splice is asserted to have landed, which a
    parallel builder could not be.

    Returns:
        The blob, with both markers present only in their wide spelling.
    """
    blob = _marker_blob(VERSION_WITH_SAVE_NAME)
    for text in ("?" + MARKER_OPTIONS + "=1", MARKER_SESSION):
        narrow = synthetic.fstring(text)
        wide = synthetic.fstring(text, wide=True)
        assert blob.count(narrow) == 1, (
            f"the {text!r} field is not in the fixture exactly once, so the splice below "
            f"would be guessing. Found {blob.count(narrow)}"
        )
        blob = blob.replace(narrow, wide, 1)
    return blob


def _marker_blob_with_an_undecodable_session_name() -> bytes:
    """A marker blob whose session name will not decode, MARKER STILL INTACT.

    `_blob_with_an_undecodable_session_name` cannot serve here, and the reason is
    the vacuity this item keeps turning up: it corrupts the FIRST byte of its own
    probe, so the slice the parser binds no longer spells anything a sweep hunts -
    and it plants no ``MARKERS`` at all. An arm sweeping that blob asks about a
    value which was never in it, and comes back empty for exactly that reason.

    MEASURED, NOT REASONED: the first cut of the arm below used it and SURVIVED
    its own mutation run - the scrub could be deleted with the suite still green,
    which is a fix with no guard.

    Here the corruption lands on a byte APPENDED AFTER the marker, so what
    ``_Cursor.string`` binds is the marker followed by one invalid byte: it will
    not decode, and it still spells the thing the sweep is looking for.

    Returns:
        The blob.
    """
    kwargs = _marker_header_kwargs(VERSION_WITH_SAVE_NAME)
    kwargs["session_name"] = MARKER_SESSION + "X"
    blob = synthetic.build_save(header_kwargs=kwargs)

    tail = (MARKER_SESSION + "X").encode("utf-8")
    assert blob.count(tail) == 1, (
        f"the session field is not in the fixture exactly once, so the corruption "
        f"below would be guessing. Found {blob.count(tail)}"
    )
    damaged = blob.replace(tail, tail[:-1] + b"\xff", 1)
    assert MARKER_SESSION.encode("utf-8") in damaged, (
        "the corruption destroyed the marker it was meant to leave standing, which "
        "is exactly what makes a sweep over it vacuous"
    )
    return damaged


def test_an_undecodable_header_string_leaves_no_frame_holding_its_bytes() -> None:
    """The one path in `_Cursor` that binds a save slice ACROSS a raise.

    `_Cursor.string` slices the declared extent into `raw`, tries to decode it,
    and raises `HeaderFormatError` FROM INSIDE that frame when it will not
    decode. `raw` is not the whole file - it is EXACTLY one header string, which
    for the options string and the session name is the platform, the account id
    and the player display name and nothing else (non-negotiable 12). Without
    the scrub a locals-showing renderer prints those bytes verbatim beside an
    error whose whole message is that they did not decode.

    NEITHER OF THIS MODULE'S OTHER TWO CS-963 ARMS CAN REACH IT. Both drive a
    TRUNCATION, which raises in `_string_extent` before `raw` is ever bound, so
    the scrubbed path and the driven path were disjoint. Found by an adversary
    reading the class rather than by any arm.
    """
    blob = _marker_blob_with_an_undecodable_session_name()

    # CONTROL: the oracle can see the marker in the bytes handed over, so an empty
    # verdict below is a measurement and not the oracle's own blindness.
    assert MARKER_SESSION in test_properties._safe_repr(blob)  # noqa: SLF001

    with pytest.raises(HeaderError) as caught:
        header_module.reveal_strings(blob, reveal_personal_data=True)
    raised = caught.value

    entered = test_properties._shipped_frame_names(raised)  # noqa: SLF001
    assert "string" in entered, (
        f"the refusal did not pass through _Cursor.string, so the scrub this arm is "
        f"about was never on the path. Frames reached: {sorted(entered)}"
    )

    for marker in MARKERS:
        leaks = test_properties._shipped_frames(raised, marker)  # noqa: SLF001
        assert not leaks, (
            f"the undecodable-string refusal leaves {marker} in a shipped frame a "
            f"renderer prints (non-negotiable 12). Offending: {leaks}"
        )


def test_the_marker_sweep_is_not_blind_to_a_wide_encoded_header_string() -> None:
    """THE ORACLE'S OWN BLIND SPOT, and it is the one that matters on a REAL save.

    Every fixture in this suite writes its header strings as UTF-8. Unreal writes
    UTF-16-LE - a NEGATIVE length count - the moment a string carries any
    non-ASCII character, which a real session name or player display name
    routinely does. The sweep's oracle looks for an ASCII marker inside
    `repr(value)`, so a wide-encoded spelling is invisible to it while a
    renderer prints the same bytes in a form a person reads at a glance.

    THAT IS THIS ITEM'S OWN DEFECT ONE LEVEL UP: an oracle that cannot observe
    the value it is asked about returns an empty verdict about itself. Every
    green privacy verdict in this layer was measured against the encoding real
    saves DO NOT use for the fields that carry personal data.

    THE ARM IS STATED AS THE POSITIVE FACT. It builds the wide-encoded blob,
    asserts the oracle is blind to the ASCII spelling - pinning the gap rather
    than assuming it - and then asserts the sweep is clean against the WIDE
    BYTES, which is the spelling that is actually in the file.
    """
    blob = _wide_marker_blob()
    wide = MARKER_OPTIONS.encode("utf-16-le")
    assert wide in blob, "the wide fixture does not carry the options marker at all"

    # THE GAP, PINNED. The ASCII spelling is genuinely absent from these bytes,
    # so an ASCII sweep over them is vacuous BY CONSTRUCTION rather than by luck.
    assert MARKER_OPTIONS.encode("ascii") not in blob, (
        "the wide fixture also carries the ASCII spelling, so it does not isolate the "
        "encoding gap this arm exists to measure"
    )

    at = blob.index(MARKER_SESSION.encode("utf-16-le"))
    cut = blob[: at + 2]
    assert wide in cut, "the cut removed the options marker, so the sweep below is vacuous"

    with pytest.raises(HeaderError) as caught:
        header_module.reveal_strings(cut, reveal_personal_data=True)
    raised = caught.value

    # The sweep asks about the bytes AS THE FILE SPELLS THEM, via the structural
    # oracle, because `repr()` of a wide slice renders escapes rather than text.
    held = test_properties._structural_holders(raised, wide)  # noqa: SLF001
    bare = test_properties._bare_holders(held)  # noqa: SLF001
    assert not bare, (
        "a shipped frame local IS the wide-encoded header string across the refusal. "
        "On a real save that is the session name or the player display name, and no "
        f"ASCII sweep in this suite can see it (non-negotiable 12): {bare}"
    )


def _wide_blob_with_an_undecodable_session_name() -> bytes:
    """A WIDE session name that will not decode, the marker still legible.

    An unpaired high surrogate is invalid UTF-16-LE, so this reaches the decode
    failure in ``_Cursor.string`` down the WIDE branch - which is the branch a real
    save takes for this field the moment a player types one non-ASCII character.

    SAME-LENGTH, replacing the last character's two bytes rather than appending,
    so the declared count still matches and the refusal is the decode rather than
    a truncation.

    Returns:
        The blob.
    """
    blob = _wide_marker_blob()
    field = synthetic.fstring(MARKER_SESSION, wide=True)
    assert blob.count(field) == 1, (
        f"the wide session field is not in the fixture exactly once, so the "
        f"corruption below would be guessing. Found {blob.count(field)}"
    )
    # The field is count + text + two null bytes; the last text character is the
    # two bytes before that terminator.
    damaged = field[:-4] + b"\x00\xd8" + field[-2:]
    assert len(damaged) == len(field)
    return blob.replace(field, damaged, 1)


def test_a_wide_undecodable_header_string_leaves_no_frame_holding_its_bytes() -> None:
    """F5 - the encoding arm, DRIVEN rather than merely built.

    The first version of this arm built a wide fixture and then drove a TRUNCATION,
    which raises in ``_string_extent`` before ``raw`` is ever bound. Wide and narrow
    produced byte-identical verdicts, and the only property it actually asserted was
    that a cursor encapsulates its buffer - which every narrow arm in this file
    already proves. An arm can carry a correct fixture and still measure nothing,
    because what a sweep grades is the frames the refusal actually enters.

    This one refuses on the DECODE, so ``_Cursor.string`` binds a slice of wide
    bytes and the scrub on that branch is on the path.

    THE GAP IS PINNED AS A POSITIVE FACT. The ASCII spelling is asserted absent
    from the bytes, so an ASCII sweep over them is vacuous BY CONSTRUCTION - which
    is the whole of CS-964 stated at one site.
    """
    blob = _wide_blob_with_an_undecodable_session_name()
    wide = MARKER_SESSION.encode("utf-16-le")

    assert MARKER_SESSION.encode("ascii") not in blob, (
        "the fixture carries the ASCII spelling too, so it does not isolate the "
        "encoding gap this arm exists to measure"
    )

    with pytest.raises(HeaderError) as caught:
        header_module.reveal_strings(blob, reveal_personal_data=True)
    raised = caught.value

    entered = test_properties._shipped_frame_names(raised)  # noqa: SLF001
    assert "string" in entered, (
        f"the refusal did not reach _Cursor.string, so no frame in this sweep ever "
        f"bound a wide slice. Frames reached: {sorted(entered)}"
    )

    held = test_properties._structural_holders(raised, wide)  # noqa: SLF001
    bare = test_properties._bare_holders(held)  # noqa: SLF001
    assert not bare, (
        "a shipped frame local IS the wide-encoded session name across the decode "
        "refusal. On a real save that is the player display name, and no ASCII "
        f"sweep in this suite can see it (non-negotiable 12): {bare}"
    )


# ---------------------------------------------------------------------------
# CS-1087 - the non-parsing scan
# ---------------------------------------------------------------------------
#
# The scan exists for exactly one population: a header the parser REFUSES,
# whose identifier is nonetheless still sitting in the bytes. So the arms here
# grade two things and keep them apart. The SHAPE arms prove that nothing but
# an identifier-shaped framed string comes back, which is the whole of the
# privacy claim - a scrape that admitted arbitrary runs would hand the commit
# gate engine strings to refuse commits on. The RECOVERY arm proves the value
# actually comes back off a save the real reader has just refused, because a
# scan that returned nothing would satisfy every shape arm perfectly.

#: A second invented token, distinct from the builder's own, for the buffers
#: below. 22 characters of base64url and a real token on no machine anywhere.
SCAN_TOKEN: Final = "Scan7Bq" + "3Vd9Nk" + "5Tz2Rm" + "8Lp"

#: The options string carries `?` and `=`, which are outside the identifier
#: alphabet. That is what makes the personal-data-bearing field unreachable
#: through this route BY SHAPE rather than by a filter someone has to maintain.
OPTIONS_TEXT: Final = "?listenServer=0?synthetic=1"


def _framed(text: str, *, wide: bool = False) -> bytes:
    """One length-prefixed string, framed the way a header frames one.

    The builder in tests/save/synthetic.py is the repository's one encoder of
    this framing, so the arms below drive IT rather than hand-packing a second
    opinion about what a frame looks like.
    """
    return synthetic.fstring(text, wide=wide)


def test_a_framed_identifier_is_recovered_without_parsing_anything() -> None:
    """The shape match, at its floor: framing plus alphabet plus terminator."""
    blob = b"\x11\x22\x33" + _framed(SCAN_TOKEN) + b"\x44\x55"

    assert header_module.scan_framed_tokens(blob) == (SCAN_TOKEN,)


@pytest.mark.parametrize(
    ("label", "blob"),
    [
        ("one character short", _framed("A" * (TOKEN_LENGTH - 1))),
        ("one character long", _framed("A" * (TOKEN_LENGTH + 1))),
        ("unframed run", b"\x00\x00\x00\x00" + ("B" * TOKEN_LENGTH).encode("ascii")),
        ("no terminator", _framed("C" * TOKEN_LENGTH)[:-1] + b"\x41"),
        ("a character outside the alphabet", _framed("D" * (TOKEN_LENGTH - 1) + "?")),
    ],
)
def test_what_is_not_an_identifier_is_never_a_candidate(label: str, blob: bytes) -> None:
    """The four near misses, one per way the frame can fail.

    Each of these is a string a real header genuinely carries somewhere - a
    shorter name, a longer one, a run with punctuation - and every one of them
    must come back empty. The length arms are the ones that matter most: a
    scan matching "22 or so" characters is a scrape wearing a shape's clothes.
    """
    assert header_module.scan_framed_tokens(blob) == (), label


def test_the_wide_framing_is_recovered_too() -> None:
    """The UTF-16-LE framing, which no measured save has ever used.

    ``_string_extent`` admits a NEGATIVE count as a character count, so a file
    written that way is legal input to this module. The scan handles it for
    that reason and for no measured one - see the docstring, which labels it
    unmeasured rather than letting a reader infer it was seen.
    """
    blob = b"\x99" + _framed(SCAN_TOKEN, wide=True) + b"\x99"

    assert header_module.scan_framed_tokens(blob) == (SCAN_TOKEN,)


def test_a_buffer_with_no_framed_string_yields_nothing() -> None:
    """The no-false-positive floor, on the suite's existing corrupt fixture.

    These are the bytes the gate's corrupt-save fixtures are made of. Nothing
    of the identifier's shape is in them at any offset, and the honest answer
    is an empty result rather than a guess.
    """
    assert header_module.scan_framed_tokens(b"\x00\xff" * 64) == ()


@pytest.mark.parametrize("length", [0, 1, TOKEN_LENGTH - 1, TOKEN_LENGTH, TOKEN_LENGTH + 1, 40])
def test_an_options_shaped_string_is_never_a_candidate(length: int) -> None:
    """ADR 0007 item 4's obligation, at every length including the exact one.

    On header version 14 the options string is the THIRD string slot, which is
    where a world name sits on versions 10 and 13 - the off-by-one the ADR
    exists for. On a real save it carries the platform, the account id and the
    player display name in plaintext (non-negotiable 12). It is out of reach
    here BY SHAPE: the alphabet holds no ``?`` and no ``=``, so no length of it
    can be mistaken for an identifier.
    """
    text = (OPTIONS_TEXT * 3)[:length]

    assert header_module.scan_framed_tokens(_framed(text)) == ()
    assert header_module.scan_framed_tokens(_framed(text, wide=True)) == ()


def test_the_per_buffer_candidate_cap_is_a_bound_that_is_crossed() -> None:
    """The cap graded by CROSSING it, never by asserting the constant exists.

    A test that planted fewer candidates than the cap would pass against an
    unbounded scan, which is the shape that grades nothing.
    """
    cap = header_module.MAX_SCANNED_TOKENS
    planted = cap + 4
    blob = b"".join(_framed("ClockspeedScanTokens%02d" % index) for index in range(planted))

    found = header_module.scan_framed_tokens(blob)

    assert cap < planted, "the fixture does not cross the bound, so this arm is vacuous"
    assert len(found) == cap, len(found)


def test_candidates_come_back_in_file_order_and_once_each() -> None:
    """Order and de-duplication, both stated by the docstring and both graded."""
    first = "ClockspeedScanTokens41"
    second = "ClockspeedScanTokens42"
    blob = _framed(second) + _framed(first) + _framed(second)

    assert header_module.scan_framed_tokens(blob) == (second, first)


def test_an_identifier_survives_a_header_the_parser_refuses(tmp_path: Path) -> None:
    """THE RECOVERY CLAIM, graded against a real refusal rather than a stub.

    ONE field is mutated - the leading int32 header version, to a value with no
    measured layout - so the parser refuses at the version prologue, before a
    single string is read. Every other byte is the builder's own, so this is
    the population the gate could not reach: a file whose identifier is intact
    and whose header will never parse.

    The refusal is DRIVEN, not assumed. An arm that only asserted the scan
    returns a token would pass just as well on a file that parses, and would
    say nothing about the case it exists for.
    """
    blob = synthetic.build_header(world_token=SCAN_TOKEN) + struct.pack("<I", synthetic.CHUNK_MAGIC)
    corrupt = struct.pack("<i", synthetic.UNSUPPORTED_HEADER_VERSION) + blob[4:]
    target = tmp_path / "unparseable.sav"
    target.write_bytes(corrupt)

    with pytest.raises(UnsupportedHeaderVersionError):
        read_header(target)

    assert header_module.scan_world_tokens(target) == (SCAN_TOKEN,)


def test_scan_world_tokens_redacts_the_path_of_a_file_it_cannot_open(tmp_path: Path) -> None:
    """The read failure, taxonomy-clean and carrying no world name.

    A save filename embeds the world name and the directory above it is the
    account id, so this is the same obligation read_header carries at the same
    raise shape - and the OSError is dropped rather than chained, because its
    message quotes the filename.
    """
    missing = tmp_path / "PlantedWorldNameNeedle.sav"

    with pytest.raises(HeaderReadError) as caught:
        header_module.scan_world_tokens(missing)

    for surface in _exception_surfaces(caught.value):
        assert "PlantedWorldNameNeedle" not in surface
    assert "<save-file>" in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None or caught.value.__suppress_context__


def test_the_scanned_prefix_is_in_no_frame_when_the_scan_unwinds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS-963's scrub, carried to the new frame that binds a save prefix.

    ``scan_world_tokens`` reads a bounded prefix, which is precisely the
    personal-data-bearing region, and its caller is a commit gate whose own
    module docstring records that a traceback there cannot be honestly
    redacted. So the one thing that must hold is that an exception unwinding
    through this frame leaves no local holding those bytes.

    THE SWEEP IS FRONTED BY A KNOWN-GOOD CONTROL, because a negative
    measurement from a sweep that cannot see anything is worth nothing: the
    same needle, in the same file, IS found in a shipped frame when the parser
    refuses it, and only then is the scanner's own frame asserted clean.
    """
    blob = synthetic.build_header(options=MARKER_OPTIONS)
    needle = MARKER_OPTIONS.encode("ascii")
    target = tmp_path / "prefix.sav"
    target.write_bytes(blob)

    with pytest.raises(HeaderError) as control:
        parse_header(blob[:-1])
    assert test_properties._structural_holders(control.value, needle), (  # noqa: SLF001
        "the control found the planted bytes in NO shipped frame, so the sweep "
        "below measures nothing at all"
    )

    def explode(_data: bytes) -> tuple[str, ...]:
        raise RuntimeError("the scan refused")

    monkeypatch.setattr(header_module, "scan_framed_tokens", explode)

    with pytest.raises(RuntimeError) as caught:
        header_module.scan_world_tokens(target)
    raised = caught.value

    entered = test_properties._shipped_frame_names(raised)  # noqa: SLF001
    assert "scan_world_tokens" in entered, sorted(entered)
    held = test_properties._structural_holders(raised, needle)  # noqa: SLF001
    assert "scan_world_tokens" not in held, held
