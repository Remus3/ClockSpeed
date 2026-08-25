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
from tests.save import synthetic

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


def _markers_present_in(blob: bytes, header_version: int) -> tuple[str, ...]:
    """Which markers the fixture actually encodes at this header version.

    Header versions 10 and 13 carry no save name, so its marker is never in
    the bytes and asserting its absence downstream would pass vacuously. This
    keeps the marker test honest about what it is actually proving.

    Args:
        blob: The fixture bytes.
        header_version: 10, 13 or 14.

    Returns:
        The markers genuinely encoded in ``blob``.
    """
    present = tuple(marker for marker in MARKERS if marker.encode("utf-8") in blob)
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
    """Assert no needle appears in any surface.

    Args:
        surfaces: Renderings to search.
        needles: The planted markers.
        where: A label naming the path under test, for the failure message.

    Raises:
        AssertionError: A needle leaked.
    """
    for needle in needles:
        for surface in surfaces:
            assert needle not in surface, f"planted marker leaked via {where}"


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


@pytest.mark.parametrize("header_version", HEADER_VERSIONS)
def test_planted_markers_never_reach_any_surface(header_version: int) -> None:
    """The load-bearing test. See the module docstring.

    Drives the success path and every failure path this module has, at every
    header version, and asserts the planted markers reach none of the surfaces
    a human or a log can read.
    """
    blob = _marker_blob(header_version)
    needles = _markers_present_in(blob, header_version)

    # --- the success path -------------------------------------------------
    parsed = parse_header(blob)
    _assert_free_of(_value_surfaces(parsed), needles, "SaveHeader on the success path")
    _assert_free_of([repr(parsed.warnings)], needles, "warnings")

    # --- truncation, at every offset in the header region ------------------
    header_length = _marker_header_length(header_version)
    for cut in range(header_length + 4):
        try:
            parse_header(synthetic.truncated_at(blob, cut))
        except HeaderError as error:
            _assert_free_of(_exception_surfaces(error), needles, f"truncation at {cut}")

    # --- a declared length above the cap -----------------------------------
    absurd = (
        blob[:FIRST_STRING_COUNT_OFFSET]
        + struct.pack("<i", synthetic.ABSURD_STRING_LENGTH)
        + blob[FIRST_STRING_COUNT_OFFSET + 4 :]
    )
    with pytest.raises(HeaderFormatError) as format_error:
        parse_header(absurd)
    _assert_free_of(_exception_surfaces(format_error.value), needles, "declared length above cap")

    # --- an unsupported version, with the markers still in the bytes -------
    kwargs = _marker_header_kwargs(header_version)
    kwargs["header_version"] = synthetic.UNSUPPORTED_HEADER_VERSION
    kwargs["with_save_name"] = True
    kwargs["with_tail"] = True
    with pytest.raises(UnsupportedHeaderVersionError) as version_error:
        parse_header(synthetic.build_save(header_kwargs=kwargs))
    _assert_free_of(_exception_surfaces(version_error.value), needles, "unsupported version")

    # --- the opt-in refusal ------------------------------------------------
    with pytest.raises(PersonalDataOptInRequiredError) as opt_in_error:
        reveal_strings(blob)
    _assert_free_of(_exception_surfaces(opt_in_error.value), needles, "opt-in refusal")

    # --- the withheld repr of the opt-in RESULT ----------------------------
    revealed = reveal_strings(blob, reveal_personal_data=True)
    _assert_free_of([repr(revealed), str(revealed)], needles, "HeaderStrings repr")


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
