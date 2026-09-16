"""CS-1097 and CS-1114 - the raw-prefix scan never admits a MEASURED save-name slot.

THE DEFECT (CS-1097). The CS-1087 scan matches a framed string by framing and
shape alone, so a player-chosen save name of exactly WORLD_TOKEN_LENGTH
characters drawn from the token alphabet is indistinguishable from the
identifier. On header 14 the save name is the FIRST string of the string
block, and the string block starts immediately after the three-int32 version
prologue on every measured header version (10, 13 and 14).

THE RESIDUES (CS-1114), AND THE RULE THAT DECIDES THEM. The scan is a
fail-safe blocklist that runs only on headers the parser REFUSES. A false
positive costs a manual unblock; a false negative leaks personal data. The
second is never traded for the first.

1. The offset-12 skip keyed on raw offset alone. It now applies only behind a
   plausible prologue whose header version is one the PARSER has a measured
   layout for AND whose layout carries a save name. An unmeasured version -
   higher or lower - never skips.
2. An arm reddens when the parser accepts a header version the slot anchor
   does not cover.
3. A 22-character SESSION name is a MEASURED, ACCEPTED false positive. It has
   no fixed offset, and finding it by walking the string chain means trusting
   a layout the parser refused. A session-slot walk was built and refuted: it
   dropped a genuine token in three synthetic layouts, pinned below as arms.

EVERY VALUE BELOW IS INVENTED and assembled from fragments. None is a real
save name, world name, account id or token (non-negotiables 3, 11 and 12).
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Final

import pytest

from clockspeed.save import header as header_module
from tests.save import synthetic

#: An INVENTED save name of exactly the measured identifier length, drawn
#: wholly from the base64url alphabet - the shape the scan cannot tell apart.
SAVE_NAME_22: Final = "Svn4Mq" + "8Hx2Pd" + "6Kw3Jr" + "5Yb1"

#: An INVENTED session name of the same shape. It has no fixed offset.
SESSION_22: Final = "Ssn7Lb" + "3Vt9Ke" + "2Np5Hc" + "8Ra4"

#: An INVENTED identifier for the same buffer. It must still come back.
TOKEN_22: Final = "Tkn9Gz" + "7Fc2Wv" + "4Qm8Ds" + "1Xh6"

#: A header version no measured layout exists for, ABOVE the save-name layout.
UNPARSEABLE_VERSION: Final = 99

#: The oracle's own statement of where slot 0 starts: three int32 fields. It
#: is derived independently of the module's constant, and the anchor arm
#: below proves it equals where the REAL parser's cursor stands.
PROLOGUE_BYTES: Final = 3 * 4

#: The header versions the anchor arms below MEASURE a layout for. The
#: coverage arm fails when the parser accepts a version outside this tuple.
COVERED_HEADER_VERSIONS: Final = (
    synthetic.HEADER_VERSION_10,
    synthetic.HEADER_VERSION_13,
    synthetic.HEADER_VERSION_14,
)

#: A version prologue with the evidence the scan requires: the measured
#: save-name header version, the builder's save version and changelist.
PLAUSIBLE_PROLOGUE: Final = struct.pack("<iii", synthetic.HEADER_VERSION_14, 60, 0)

#: A span over which the coverage arm probes the parser's version check. It
#: reaches well past every measured version in both directions.
PROBED_VERSIONS: Final = range(-64, 4096)

#: Prefixes that are NOT evidence of a save name at slot 0, each named for the
#: field that disqualifies it. A value framed at offset 12 behind any of them
#: must still be admitted.
NON_PROLOGUE_PREFIXES: Final = {
    "all-zero bytes": bytes(PROLOGUE_BYTES),
    "header version below every measured one": struct.pack("<iii", 3, 60, 0),
    "unmeasured header version between layouts": struct.pack("<iii", 12, 60, 0),
    "unmeasured header version just above 14": struct.pack("<iii", 15, 60, 0),
    "unmeasured header version far above 14": struct.pack("<iii", UNPARSEABLE_VERSION, 60, 0),
    "header version at the int32 ceiling": struct.pack("<iii", 0x7FFFFFFF, 60, 0),
    "negative header version": struct.pack("<iii", -14, 60, 0),
    "save version zero": struct.pack("<iii", 14, 0, 0),
    "negative save version": struct.pack("<iii", 14, -60, 0),
    "save version at the int32 ceiling": struct.pack("<iii", 14, 0x7FFFFFFF, 0),
    "negative build changelist": struct.pack("<iii", 14, 60, -1),
    "measured version whose slot 0 is the map name": struct.pack("<iii", 13, 42, 0),
    "printable text": b"not a header",
}


def _with_version(blob: bytes, version: int) -> bytes:
    """Overwrite the leading header version."""
    return struct.pack("<i", version) + blob[4:]


def _rewiden(blob: bytes, text: str) -> bytes:
    """Re-encode the one narrow frame of ``text`` in ``blob`` as a wide frame."""
    narrow = synthetic.fstring(text)
    assert blob.count(narrow) == 1, "the fixture frames the value more than once"
    return blob.replace(narrow, synthetic.fstring(text, wide=True))


def _header_with_save_name(*, wide: bool = False) -> bytes:
    """A header-14 layout, refused for want of a chunk magic, SAVE_NAME_22 at slot 0."""
    blob = synthetic.build_header(save_name=SAVE_NAME_22, world_token=TOKEN_22)
    return _rewiden(blob, SAVE_NAME_22) if wide else blob


def _layout(layout_version: int, *, wide: bool = False) -> bytes:
    """A measured layout carrying SESSION_22 and, on 14, SAVE_NAME_22."""
    blob = synthetic.build_header(
        header_version=layout_version,
        save_name=SAVE_NAME_22,
        session_name=SESSION_22,
        world_token=TOKEN_22,
    )
    if wide:
        blob = _rewiden(blob, SESSION_22)
        if layout_version >= synthetic.HEADER_VERSION_WITH_SAVE_NAME:
            blob = _rewiden(blob, SAVE_NAME_22)
    return blob


def _decoy(index: int) -> str:
    """An invented 22-character alphabet value, distinct per index."""
    value = "Decoy" + "Candidate" + "Value" + "x%02d" % index
    assert len(value) == header_module.WORLD_TOKEN_LENGTH
    return value


def _fixed_block() -> bytes:
    """The fixed block between the session name and the identifier, empty mod metadata."""
    return (
        struct.pack("<i", 1)
        + struct.pack("<q", 2)
        + b"\x00"
        + struct.pack("<i", 40)
        + synthetic.fstring("")
        + struct.pack("<i", 0)
    )


# ---------------------------------------------------------------------------
# CS-1097 - the save name at slot 0, on the measured layout
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("wide", [False, True], ids=["narrow", "wide"])
def test_a_save_name_at_slot_zero_is_not_a_candidate_while_the_token_is(wide: bool) -> None:
    """A1 and A2: the save name is refused, the identifier in the SAME buffer is not."""
    blob = _header_with_save_name(wide=wide)
    # The fixture places the save name where the arm says it does, or the arm
    # grades a buffer it never built.
    assert blob[PROLOGUE_BYTES:].startswith(synthetic.fstring(SAVE_NAME_22, wide=wide))
    with pytest.raises(header_module.HeaderTruncatedError):
        header_module.parse_header(blob)

    candidates, truncated = header_module.scan_framed_tokens(blob)

    save_name_admitted = SAVE_NAME_22 in candidates
    token_found = TOKEN_22 in candidates
    assert not save_name_admitted, "the slot-0 save name was admitted as a token candidate"
    assert token_found, "the genuine identifier in the same buffer was dropped"
    assert candidates == (TOKEN_22,)
    assert truncated is False


def test_the_file_anchored_scan_refuses_the_save_name_too(tmp_path: Path) -> None:
    """The same property through the path-reading entry the gate calls."""
    target = tmp_path / "slot-zero.sav"
    target.write_bytes(_header_with_save_name())

    candidates, truncated = header_module.scan_world_tokens(target)

    assert candidates == (TOKEN_22,)
    assert truncated is False


@pytest.mark.parametrize("version", [UNPARSEABLE_VERSION, 15])
def test_a_save_name_behind_an_unmeasured_version_is_an_accepted_false_positive(
    version: int,
) -> None:
    """No measured layout, no skip: the save name is admitted beside the token."""
    blob = _with_version(_header_with_save_name(), version)

    assert header_module.scan_framed_tokens(blob) == ((SAVE_NAME_22, TOKEN_22), False)


def test_a_header_without_a_save_name_still_yields_its_token() -> None:
    """A3b, anti-narrowing: header 10 has no save name, and the token returns."""
    blob = _with_version(
        synthetic.build_header(header_version=synthetic.HEADER_VERSION_10, world_token=TOKEN_22),
        UNPARSEABLE_VERSION,
    )

    assert header_module.scan_framed_tokens(blob) == ((TOKEN_22,), False)


def test_the_default_header_14_layout_still_yields_its_token() -> None:
    """A3a, anti-narrowing: the builder's own header-14 buffer, save name included."""
    blob = synthetic.build_header(world_token=TOKEN_22)

    assert header_module.scan_framed_tokens(blob) == ((TOKEN_22,), False)


@pytest.mark.parametrize("wide", [False, True], ids=["narrow", "wide"])
@pytest.mark.parametrize("offset", [PROLOGUE_BYTES - 1, PROLOGUE_BYTES + 1])
def test_a_candidate_one_byte_either_side_of_slot_zero_is_still_admitted(
    offset: int, wide: bool
) -> None:
    """A3c: POSITION is what is excluded, not the value and not a neighbourhood."""
    prefix = (PLAUSIBLE_PROLOGUE + b"\x00")[:offset]
    blob = prefix + synthetic.fstring(SAVE_NAME_22, wide=wide) + b"\x7f"

    assert header_module.scan_framed_tokens(blob) == ((SAVE_NAME_22,), False)


@pytest.mark.parametrize("wide", [False, True], ids=["narrow", "wide"])
def test_a_candidate_at_slot_zero_behind_a_plausible_prologue_is_refused(wide: bool) -> None:
    """The positional twin of A3c: the SAME framed value, at offset 12, is refused."""
    blob = PLAUSIBLE_PROLOGUE + synthetic.fstring(SAVE_NAME_22, wide=wide) + b"\x7f"

    assert header_module.scan_framed_tokens(blob) == ((), False)


@pytest.mark.parametrize("wide", [False, True], ids=["narrow", "wide"])
def test_the_refused_slot_spends_no_candidate_budget(wide: bool) -> None:
    """A4: a save name at slot 0 plus exactly MAX_SCANNED_TOKENS later candidates."""
    cap = header_module.MAX_SCANNED_TOKENS
    decoys = [_decoy(index) for index in range(cap - 1)]
    later = [*decoys, TOKEN_22]
    blob = (
        PLAUSIBLE_PROLOGUE
        + synthetic.fstring(SAVE_NAME_22, wide=wide)
        + b"".join(synthetic.fstring(value, wide=wide) for value in later)
    )

    candidates, truncated = header_module.scan_framed_tokens(blob)

    token_found = TOKEN_22 in candidates
    save_name_admitted = SAVE_NAME_22 in candidates
    assert token_found, "the identifier was pushed past the cap by a refused slot"
    assert not save_name_admitted
    assert truncated is False
    assert candidates == tuple(later)


# ---------------------------------------------------------------------------
# CS-1114 residue 1 - the skip needs evidence, not just an offset
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("wide", [False, True], ids=["narrow", "wide"])
@pytest.mark.parametrize("label", sorted(NON_PROLOGUE_PREFIXES))
def test_a_token_at_offset_12_behind_a_non_prologue_prefix_is_admitted(
    label: str, wide: bool
) -> None:
    """Offset 12 is refused only where the bytes before it say it holds a save name."""
    blob = NON_PROLOGUE_PREFIXES[label] + synthetic.fstring(TOKEN_22, wide=wide) + b"\x7f"
    assert len(NON_PROLOGUE_PREFIXES[label]) == PROLOGUE_BYTES, label

    candidates, truncated = header_module.scan_framed_tokens(blob)

    token_found = TOKEN_22 in candidates
    assert token_found, "a token at offset 12 was dropped with no prologue to justify it: " + label
    assert truncated is False


# ---------------------------------------------------------------------------
# The refuted session-slot walk - three leaks, pinned as arms
# ---------------------------------------------------------------------------


def test_a_token_in_the_session_slot_of_a_between_layouts_version_is_found() -> None:
    """Leak 1: header 12 + map name + options + token, the walk read it as 10/13's."""
    blob = (
        struct.pack("<iii", 12, 46, 1)
        + synthetic.fstring(synthetic.MAP_NAME)
        + synthetic.fstring(synthetic.SYNTHETIC_OPTIONS)
        + synthetic.fstring(TOKEN_22)
    )

    candidates, _truncated = header_module.scan_framed_tokens(blob)

    token_found = TOKEN_22 in candidates
    assert token_found, "LEAK: a token in a guessed session slot was dropped (version 12)"


def test_a_token_in_the_session_slot_of_a_higher_version_is_found() -> None:
    """Leak 2: header 15 + save name + map + options + token, the >= 14 extrapolation."""
    blob = (
        struct.pack("<iii", 15, 50, 1)
        + synthetic.fstring(SAVE_NAME_22)
        + synthetic.fstring(synthetic.MAP_NAME)
        + synthetic.fstring(synthetic.SYNTHETIC_OPTIONS)
        + synthetic.fstring(TOKEN_22)
    )

    candidates, _truncated = header_module.scan_framed_tokens(blob)

    token_found = TOKEN_22 in candidates
    assert token_found, "LEAK: a token in a guessed session slot was dropped (version 15)"


def test_a_token_reached_by_an_oversize_options_count_is_found() -> None:
    """Leak 3: header 14 whose options count spans to the token's prefix."""
    options = synthetic.SYNTHETIC_OPTIONS.encode("ascii") + b"\x00"
    spanned = options + synthetic.fstring("Synthetic Session") + _fixed_block()
    blob = (
        PLAUSIBLE_PROLOGUE
        + synthetic.fstring("SyntheticSave")
        + synthetic.fstring(synthetic.MAP_NAME)
        + struct.pack("<i", len(spanned))
        + spanned
        + synthetic.fstring(TOKEN_22)
    )
    assert len(spanned) <= header_module.MAX_STRING_BYTES, "the count must still frame"

    candidates, _truncated = header_module.scan_framed_tokens(blob)

    token_found = TOKEN_22 in candidates
    assert token_found, "LEAK: a token reached by an oversize options count was dropped"


# ---------------------------------------------------------------------------
# CS-1114 residue 3 - the session name is a measured, accepted false positive
# ---------------------------------------------------------------------------

#: Each measured layout, paired with a header version its bytes are read under.
LAYOUT_READINGS: Final = [
    (synthetic.HEADER_VERSION_10, synthetic.HEADER_VERSION_10),
    (synthetic.HEADER_VERSION_10, 11),
    (synthetic.HEADER_VERSION_13, synthetic.HEADER_VERSION_13),
    (synthetic.HEADER_VERSION_13, 12),
    (synthetic.HEADER_VERSION_14, synthetic.HEADER_VERSION_14),
    (synthetic.HEADER_VERSION_14, UNPARSEABLE_VERSION),
]


@pytest.mark.parametrize("wide", [False, True], ids=["narrow", "wide"])
@pytest.mark.parametrize(("layout_version", "read_as"), LAYOUT_READINGS)
def test_a_session_name_is_still_admitted_and_the_token_is_found_in_every_layout(
    layout_version: int, read_as: int, wide: bool
) -> None:
    """Residue 3 pinned as a documented limit, with the anti-narrowing control.

    The session name comes back as a candidate on every layout - the accepted
    false positive - and so does the identifier, which is what stops a
    reject-everything scan passing.
    """
    blob = _with_version(_layout(layout_version, wide=wide), read_as)

    candidates, truncated = header_module.scan_framed_tokens(blob)

    session_admitted = SESSION_22 in candidates
    token_found = TOKEN_22 in candidates
    assert session_admitted, "the session name was refused; that walk trusts a refused layout"
    assert token_found, "the genuine identifier was dropped"
    assert truncated is False


# ---------------------------------------------------------------------------
# The anchors - the refused offset is the parser's layout, per version
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("version", COVERED_HEADER_VERSIONS)
def test_the_excluded_offset_is_where_the_parser_starts_the_string_block(version: int) -> None:
    """The offset is the parser's own layout, measured per supported version."""
    cursor = header_module._Cursor(synthetic.build_header(header_version=version))  # noqa: SLF001
    header_module._version_prologue(cursor)  # noqa: SLF001

    assert cursor.offset == PROLOGUE_BYTES
    assert cursor.offset == header_module.FIRST_STRING_SLOT_OFFSET


@pytest.mark.parametrize("version", COVERED_HEADER_VERSIONS)
def test_the_refused_offsets_are_exactly_the_parsers_save_name_slot(version: int) -> None:
    """The refused offset is where the PARSER decodes a save name, and nothing else."""
    blob = _layout(version)
    strings = header_module.reveal_strings(blob, reveal_personal_data=True)
    parser_has_save_name = strings.save_name is not None
    if parser_has_save_name:
        save_name_decoded = strings.save_name == SAVE_NAME_22
        assert save_name_decoded, "the builder and the parser disagree on the save-name slot"
    expected = {PROLOGUE_BYTES} if parser_has_save_name else set()

    refused = header_module._personal_slot_offsets(blob)  # noqa: SLF001

    assert refused == frozenset(expected)


# ---------------------------------------------------------------------------
# CS-1114 residue 2 - an accepted version the anchors do not cover reddens
# ---------------------------------------------------------------------------


def _parser_accepted_versions() -> set[int]:
    """The header versions the REAL prologue reader accepts, by driving it."""
    accepted: set[int] = set()
    for version in PROBED_VERSIONS:
        cursor = header_module._Cursor(struct.pack("<iii", version, 60, 0))  # noqa: SLF001
        try:
            header_module._version_prologue(cursor)  # noqa: SLF001
        except header_module.UnsupportedHeaderVersionError:
            continue
        accepted.add(version)
    # A version outside the probed span is still one the parser names.
    accepted.update(header_module.SUPPORTED_HEADER_VERSIONS)
    return accepted


def test_every_header_version_the_parser_accepts_is_covered_by_the_anchors() -> None:
    """A newly accepted version reddens until the anchors measure its layout."""
    accepted = _parser_accepted_versions()
    uncovered = sorted(accepted - set(COVERED_HEADER_VERSIONS))

    assert accepted, "the probe found no accepted version, so it measured nothing"
    assert uncovered == [], f"accepted header versions with no slot anchor: {uncovered}"


def test_no_version_the_parser_refuses_ever_skips_slot_zero() -> None:
    """Over the whole probed span, a refused version never refuses offset 12."""
    accepted = _parser_accepted_versions()
    body = synthetic.fstring(SAVE_NAME_22) + b"\x7f"
    skipping_refused = [
        version
        for version in PROBED_VERSIONS
        if version not in accepted
        and header_module._personal_slot_offsets(  # noqa: SLF001
            struct.pack("<iii", version, 60, 0) + body
        )
    ]

    skipping_count = len(skipping_refused)
    first_skipping = skipping_refused[:5]
    assert skipping_count == 0, f"{skipping_count} refused versions skip slot 0: {first_skipping}"
