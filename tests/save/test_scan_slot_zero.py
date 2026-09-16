"""CS-1097 - the raw-prefix scan never admits the FIRST string slot.

THE DEFECT. The CS-1087 scan matches a framed string by framing and shape
alone, so a player-chosen save name of exactly WORLD_TOKEN_LENGTH characters
drawn from the token alphabet is indistinguishable from the identifier. On
header 14 the save name is the FIRST string of the string block, and the
string block starts immediately after the three-int32 version prologue on
every measured header version (10, 13 and 14). The identifier is the LAST
string, after the fixed block, and is never in that slot on any measured
layout.

THE FIX IS A POSITION, NOT A VALUE. A candidate whose count prefix starts at
the first string-slot offset is not admitted, in both framings, BEFORE it is
decoded and BEFORE it can spend a slot of the per-framing candidate cap.

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


def _unparseable(blob: bytes) -> bytes:
    """Overwrite the header version with one the parser refuses."""
    return struct.pack("<i", UNPARSEABLE_VERSION) + blob[4:]


def _header_with_save_name(*, wide: bool = False) -> bytes:
    """A header-14 layout whose slot 0 is SAVE_NAME_22, then TOKEN_22 last."""
    without = synthetic.build_header(world_token=TOKEN_22, with_save_name=False)
    blob = (
        without[:PROLOGUE_BYTES]
        + synthetic.fstring(SAVE_NAME_22, wide=wide)
        + without[PROLOGUE_BYTES:]
    )
    return _unparseable(blob)


def _decoy(index: int) -> str:
    """An invented 22-character alphabet value, distinct per index."""
    value = "Decoy" + "Candidate" + "Value" + "x%02d" % index
    assert len(value) == header_module.WORLD_TOKEN_LENGTH
    return value


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
    """A3c: POSITION is what is excluded, not the value and not a neighbourhood."""
    blob = b"\x00" * offset + synthetic.fstring(SAVE_NAME_22, wide=wide) + b"\x7f"

    assert header_module.scan_framed_tokens(blob) == ((SAVE_NAME_22,), False)


@pytest.mark.parametrize("wide", [False, True], ids=["narrow", "wide"])
def test_a_candidate_exactly_at_slot_zero_is_refused_whatever_its_value(wide: bool) -> None:
    """The positional twin of A3c: the SAME framed value, at offset 12, is refused."""
    blob = b"\x00" * PROLOGUE_BYTES + synthetic.fstring(SAVE_NAME_22, wide=wide) + b"\x7f"

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
    blob = _unparseable(
        b"\x00" * PROLOGUE_BYTES
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


@pytest.mark.parametrize(
    "version",
    [synthetic.HEADER_VERSION_10, synthetic.HEADER_VERSION_13, synthetic.HEADER_VERSION_14],
)
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
