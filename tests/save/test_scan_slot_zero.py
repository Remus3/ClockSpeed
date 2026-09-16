"""CS-1097 and CS-1114 - the raw-prefix scan never admits a personal string slot.

THE DEFECT (CS-1097). The CS-1087 scan matches a framed string by framing and
shape alone, so a player-chosen save name of exactly WORLD_TOKEN_LENGTH
characters drawn from the token alphabet is indistinguishable from the
identifier. On header 14 the save name is the FIRST string of the string
block, and the string block starts immediately after the three-int32 version
prologue on every measured header version (10, 13 and 14). The identifier is
the LAST string, after the fixed block, and is never in that slot on any
measured layout.

THE RESIDUES (CS-1114). The CS-1097 skip keyed on raw offset ALONE, so:

1. a token framed at offset 12 behind bytes that are no version prologue at
   all was dropped from the blocklist. The skip is now conditioned on a
   PLAUSIBLE prologue read from the same bytes, and on a header version whose
   layout puts a save name in that slot;
2. nothing reddened when the parser came to accept a header version the
   slot-offset anchor below does not measure. The accepted set is now derived
   from the parser's own behaviour and compared with the covered set;
3. a 22-character SESSION name, which has no fixed offset, was admitted. The
   parser's own field order puts it after a fixed number of framed strings,
   so the scan now walks that chain from slot 0 and refuses the slot it lands
   on - only behind a plausible prologue, and only if every string before it
   frames.

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

#: The header version no measured layout exists for, so the real parser
#: refuses at the prologue - the population the scan exists for. Spelled here
#: rather than imported from the module under test.
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

#: A version prologue with the evidence the scan requires: an unmeasured
#: header version at or above the save-name layout, the builder's own save
#: version and build changelist. The parser REFUSES it at the first field.
PLAUSIBLE_PROLOGUE: Final = struct.pack("<iii", UNPARSEABLE_VERSION, 60, 0)

#: A span over which the coverage arm probes the parser's version check. It
#: reaches well past every measured version in both directions.
PROBED_VERSIONS: Final = range(-64, 4096)

#: Prefixes that are NOT evidence of a save name at slot 0, each named for the
#: field that disqualifies it. A value framed at offset 12 behind any of them
#: must still be admitted.
NON_PROLOGUE_PREFIXES: Final = {
    "all-zero bytes": bytes(PROLOGUE_BYTES),
    "header version below every measured one": struct.pack("<iii", 3, 60, 0),
    "header version at the int32 ceiling": struct.pack("<iii", 0x7FFFFFFF, 60, 0),
    "negative header version": struct.pack("<iii", -14, 60, 0),
    "save version zero": struct.pack("<iii", UNPARSEABLE_VERSION, 0, 0),
    "negative save version": struct.pack("<iii", UNPARSEABLE_VERSION, -60, 0),
    "save version at the int32 ceiling": struct.pack("<iii", UNPARSEABLE_VERSION, 0x7FFFFFFF, 0),
    "negative build changelist": struct.pack("<iii", UNPARSEABLE_VERSION, 60, -1),
    "measured version whose slot 0 is the map name": struct.pack(
        "<iii", synthetic.HEADER_VERSION_13, 42, 0
    ),
    "printable text": b"not a header",
}


def _unparseable(blob: bytes, version: int = UNPARSEABLE_VERSION) -> bytes:
    """Overwrite the header version with one the parser refuses."""
    return struct.pack("<i", version) + blob[4:]


def _rewiden(blob: bytes, text: str) -> bytes:
    """Re-encode the one narrow frame of ``text`` in ``blob`` as a wide frame."""
    narrow = synthetic.fstring(text)
    assert blob.count(narrow) == 1, "the fixture frames the value more than once"
    return blob.replace(narrow, synthetic.fstring(text, wide=True))


def _header_with_save_name(*, wide: bool = False) -> bytes:
    """A header-14 layout whose slot 0 is SAVE_NAME_22, then TOKEN_22 last."""
    without = synthetic.build_header(world_token=TOKEN_22, with_save_name=False)
    blob = (
        without[:PROLOGUE_BYTES]
        + synthetic.fstring(SAVE_NAME_22, wide=wide)
        + without[PROLOGUE_BYTES:]
    )
    return _unparseable(blob)


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


# ---------------------------------------------------------------------------
# CS-1097 - the save name at slot 0
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("wide", [False, True], ids=["narrow", "wide"])
def test_a_save_name_at_slot_zero_is_not_a_candidate_while_the_token_is(wide: bool) -> None:
    """A1 and A2: the save name is refused, the identifier in the SAME buffer is not."""
    blob = _header_with_save_name(wide=wide)
    # The fixture places the save name where the arm says it does, or the arm
    # grades a buffer it never built.
    assert blob[PROLOGUE_BYTES:].startswith(synthetic.fstring(SAVE_NAME_22, wide=wide))

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
    target.write_bytes(_header_with_save_name() + struct.pack("<I", synthetic.CHUNK_MAGIC))

    candidates, truncated = header_module.scan_world_tokens(target)

    assert candidates == (TOKEN_22,)
    assert truncated is False


def test_a_header_without_a_save_name_still_yields_its_token() -> None:
    """A3b, anti-narrowing: header 10 has no save name, and the token returns.

    A rule keyed on "the first candidate in file order" rather than on the
    offset would drop this identifier, because it is the first candidate here.
    """
    blob = _unparseable(
        synthetic.build_header(header_version=synthetic.HEADER_VERSION_10, world_token=TOKEN_22)
    )

    assert header_module.scan_framed_tokens(blob) == ((TOKEN_22,), False)


def test_the_default_header_14_layout_still_yields_its_token() -> None:
    """A3a, anti-narrowing: the builder's own header-14 buffer, save name included."""
    blob = _unparseable(synthetic.build_header(world_token=TOKEN_22))

    assert header_module.scan_framed_tokens(blob) == ((TOKEN_22,), False)


@pytest.mark.parametrize("wide", [False, True], ids=["narrow", "wide"])
@pytest.mark.parametrize("offset", [PROLOGUE_BYTES - 1, PROLOGUE_BYTES + 1])
def test_a_candidate_one_byte_either_side_of_slot_zero_is_still_admitted(
    offset: int, wide: bool
) -> None:
    """A3c: POSITION is what is excluded, not the value and not a neighbourhood.

    The prefix is the PLAUSIBLE prologue cut or padded to the offset, so the
    arm is not satisfied merely by the prologue failing its evidence check.
    """
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
    """A4: a save name at slot 0 plus exactly MAX_SCANNED_TOKENS later candidates.

    The genuine identifier is the LAST of them. A refusal applied after the
    cap test lets the save name spend one slot, so the identifier is the one
    candidate past the cap and is dropped with the truncation flag raised.
    """
    cap = header_module.MAX_SCANNED_TOKENS
    decoys = [_decoy(index) for index in range(cap - 1)]
    later = [*decoys, TOKEN_22]
    # The map, options and session strings a header-14 layout frames next, so
    # the session-slot refusal lands on a string that is no candidate at all
    # and this arm grades the slot-0 refusal alone.
    blob = (
        PLAUSIBLE_PROLOGUE
        + synthetic.fstring(SAVE_NAME_22, wide=wide)
        + synthetic.fstring(synthetic.MAP_NAME)
        + synthetic.fstring(synthetic.SYNTHETIC_OPTIONS)
        + synthetic.fstring(synthetic.SYNTHETIC_SESSION_NAME)
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


def test_the_non_prologue_arm_is_not_satisfied_by_a_scan_that_skips_nothing() -> None:
    """The control: the same value, behind the plausible prologue, IS refused.

    Without it, every arm above passes on a scan with no slot-0 rule at all.
    """
    blob = PLAUSIBLE_PROLOGUE + synthetic.fstring(TOKEN_22) + b"\x7f"

    assert header_module.scan_framed_tokens(blob) == ((), False)


# ---------------------------------------------------------------------------
# CS-1114 residue 3 - the session name, by the parser's own field order
# ---------------------------------------------------------------------------

#: Each measured layout, paired with the header versions its bytes are read
#: under: its own (the parser accepts it; the scan still meets it when a later
#: field refuses) and an unmeasured one the parser refuses at the prologue.
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
def test_a_session_name_is_refused_and_the_token_is_found_in_every_layout(
    layout_version: int, read_as: int, wide: bool
) -> None:
    """Residue 3 closed, with the anti-narrowing control in the same assertion.

    The session name AND (on 14) the save name are identifier-shaped, so only
    the identifier may come back - and it must come back on every measured
    layout, which is what stops a reject-everything scan passing.
    """
    blob = _unparseable(_layout(layout_version, wide=wide), read_as)

    candidates, truncated = header_module.scan_framed_tokens(blob)

    session_admitted = SESSION_22 in candidates
    token_found = TOKEN_22 in candidates
    assert not session_admitted, "a session name was admitted as a token candidate"
    assert token_found, "the genuine identifier was dropped"
    assert candidates == (TOKEN_22,)
    assert truncated is False


@pytest.mark.parametrize("wide", [False, True], ids=["narrow", "wide"])
def test_the_refused_session_slot_spends_no_candidate_budget(wide: bool) -> None:
    """The session refusal happens before the cap, exactly as slot 0's does."""
    cap = header_module.MAX_SCANNED_TOKENS
    blob = _unparseable(_layout(synthetic.HEADER_VERSION_14, wide=wide))
    decoys = [_decoy(index) for index in range(cap - 2)]
    blob += b"".join(synthetic.fstring(value, wide=wide) for value in decoys)
    blob += synthetic.fstring(TOKEN_22.swapcase(), wide=wide)

    candidates, truncated = header_module.scan_framed_tokens(blob)

    last_found = TOKEN_22.swapcase() in candidates
    assert last_found, "the last genuine candidate was pushed past the cap by a refused slot"
    assert truncated is False
    assert len(candidates) == cap


@pytest.mark.parametrize("wide", [False, True], ids=["narrow", "wide"])
def test_a_session_slot_behind_a_non_prologue_prefix_is_admitted(wide: bool) -> None:
    """The chain walk needs the same evidence the slot-0 skip does."""
    blob = bytes(PROLOGUE_BYTES) + _layout(synthetic.HEADER_VERSION_14, wide=wide)[PROLOGUE_BYTES:]

    candidates, _truncated = header_module.scan_framed_tokens(blob)

    session_found = SESSION_22 in candidates
    assert session_found, "a session-slot value was refused with no prologue to justify it"


@pytest.mark.parametrize("version", [3, -14], ids=["below-measured", "negative"])
def test_a_session_slot_behind_a_header_version_below_every_layout_is_admitted(
    version: int,
) -> None:
    """No layout is known below the oldest measured header, so no slot is refused.

    The slot-0 arms cannot see this bound: below header 14 no save name is
    refused anyway, so only the session slot grades the header-version floor.
    """
    blob = _unparseable(_layout(synthetic.HEADER_VERSION_10), version)

    candidates, _truncated = header_module.scan_framed_tokens(blob)

    session_found = SESSION_22 in candidates
    assert session_found, "a session slot was refused behind a header version with no layout"


def test_a_session_slot_after_a_string_that_does_not_frame_is_admitted() -> None:
    """The walk stops at a broken frame rather than guessing where slot 3 is.

    The options string's count is replaced by one above the module's string
    cap, so no layout-following reader could step over it.
    """
    blob = _unparseable(_layout(synthetic.HEADER_VERSION_14))
    options = synthetic.fstring(synthetic.SYNTHETIC_OPTIONS)
    at = blob.index(options)
    broken = blob[:at] + struct.pack("<i", 0x7FFFFFF0) + blob[at + 4 :]

    candidates, _truncated = header_module.scan_framed_tokens(broken)

    session_found = SESSION_22 in candidates
    assert session_found, "a session slot was refused though the chain to it did not frame"


# ---------------------------------------------------------------------------
# The anchors - the refused offsets are the parser's layout, per version
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("version", COVERED_HEADER_VERSIONS)
def test_the_excluded_offset_is_where_the_parser_starts_the_string_block(version: int) -> None:
    """The offset is the parser's own layout, measured per supported version.

    The real prologue reader is driven over a real builder header, and where
    its cursor stands afterwards is where slot 0 begins. The module constant
    must equal it on every measured version, so the refusal cannot drift from
    the layout it is justified by.
    """
    cursor = header_module._Cursor(synthetic.build_header(header_version=version))  # noqa: SLF001
    header_module._version_prologue(cursor)  # noqa: SLF001

    assert cursor.offset == PROLOGUE_BYTES
    assert cursor.offset == header_module.FIRST_STRING_SLOT_OFFSET


@pytest.mark.parametrize("version", COVERED_HEADER_VERSIONS)
def test_the_refused_offsets_are_the_parsers_save_and_session_slots(version: int) -> None:
    """The refused offsets equal where the builder framed the two names.

    The builder's placement is itself checked against the PARSER: the opt-in
    reader, which walks the string block in the parser's field order, must
    decode the planted values out of exactly those slots.
    """
    blob = _layout(version)
    strings = header_module.reveal_strings(blob, reveal_personal_data=True)
    session_decoded = strings.session_name == SESSION_22
    save_name_decoded = strings.save_name == (
        SAVE_NAME_22 if version >= synthetic.HEADER_VERSION_WITH_SAVE_NAME else None
    )
    assert session_decoded, "the builder and the parser disagree on the session slot"
    assert save_name_decoded, "the builder and the parser disagree on the save-name slot"

    expected = {blob.index(synthetic.fstring(SESSION_22))}
    if version >= synthetic.HEADER_VERSION_WITH_SAVE_NAME:
        expected.add(blob.index(synthetic.fstring(SAVE_NAME_22)))

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


def test_every_accepted_header_version_counts_as_prologue_evidence() -> None:
    """A version the parser accepts must never read as a non-prologue prefix.

    Otherwise a header the parser would dispatch - but which a later field
    refuses - loses its save-name and session-name refusals silently.
    """
    for version in sorted(_parser_accepted_versions()):
        blob = _layout(version)
        refused = header_module._personal_slot_offsets(blob)  # noqa: SLF001
        assert refused, f"header version {version} gave the scan no slot evidence"
