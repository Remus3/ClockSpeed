"""CS-1097 and CS-1114 at the gate rung - a personal name never becomes a blocklist entry.

The ROADMAP acceptance names this arm: a save name of exactly the measured
length must NOT become a blocklist entry while a real identifier in the same
buffer still does. CS-1114 adds the converse: a token framed at offset 12
behind bytes that are no measured save-name prologue, or in a guessed
session slot, is STILL blocklisted - and a 22-character session name is a
measured, accepted false positive that IS blocklisted. Each is graded on a
REAL unparseable save written under a temporary save root, never on a
patched reader.

The helpers are imported from tests/test_precommit_gate.py by name. No test
function is imported, so nothing collects twice.

EVERY VALUE BELOW IS INVENTED and assembled from fragments. None is a real
save name, world name, account id or token (non-negotiables 3, 11 and 12).
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Final

import pytest

from tests.save import synthetic
from tests.test_precommit_gate import (
    FAKE_ACCOUNT_ID,
    base_env,
    leak_diagnostics,
    load_gate,
    make_save_root,
    pin_save_root,
    run_gate,
    write,
)

#: An INVENTED save name of the measured identifier length, alphabet-only.
SAVE_NAME_22: Final = "Svn4Mq" + "8Hx2Pd" + "6Kw3Jr" + "5Yb1"

#: An INVENTED session name of the same shape, which has no fixed offset.
SESSION_22: Final = "Ssn7Lb" + "3Vt9Ke" + "2Np5Hc" + "8Ra4"

#: An INVENTED identifier carried by the same unparseable header.
TOKEN_22: Final = "Tkn9Gz" + "7Fc2Wv" + "4Qm8Ds" + "1Xh6"

#: The `.sav` basename. Shares no substring with either staged value, so a
#: block can only be attributed to the header scan and never to a world name.
SAVE_STEM: Final = "Quill" + "stone"


def _save_root_with_named_unparseable_save(tmp_path: Path) -> Path:
    """A save root whose one header-14 save refuses to parse and carries all three values.

    The header version is the MEASURED save-name layout; the refusal comes from
    the missing chunk magic, so the string block is exactly the parser's.
    """
    blob = synthetic.build_header(
        save_name=SAVE_NAME_22, session_name=SESSION_22, world_token=TOKEN_22
    )
    return _save_root_holding(tmp_path, blob)


def _options_spanning_to(token: str) -> bytes:
    """Header 14 whose options count spans the session name and fixed block."""
    options = synthetic.SYNTHETIC_OPTIONS.encode("ascii") + b"\x00"
    fixed = (
        struct.pack("<i", 1)
        + struct.pack("<q", 2)
        + b"\x00"
        + struct.pack("<i", 40)
        + synthetic.fstring("")
        + struct.pack("<i", 0)
    )
    spanned = options + synthetic.fstring("Synthetic Session") + fixed
    return (
        struct.pack("<iii", 14, 60, 0)
        + synthetic.fstring("SyntheticSave")
        + synthetic.fstring(synthetic.MAP_NAME)
        + struct.pack("<i", len(spanned))
        + spanned
        + synthetic.fstring(token)
    )


#: The three layouts an adversary measured leaking a token through a guessed
#: session-slot walk (CS-1114). Each must blocklist the token.
LEAK_LAYOUTS: Final = {
    "version 12, token in the guessed session slot": (
        struct.pack("<iii", 12, 46, 1)
        + synthetic.fstring(synthetic.MAP_NAME)
        + synthetic.fstring(synthetic.SYNTHETIC_OPTIONS)
        + synthetic.fstring(TOKEN_22)
    ),
    "version 15, token in the guessed session slot": (
        struct.pack("<iii", 15, 50, 1)
        + synthetic.fstring(SAVE_NAME_22)
        + synthetic.fstring(synthetic.MAP_NAME)
        + synthetic.fstring(synthetic.SYNTHETIC_OPTIONS)
        + synthetic.fstring(TOKEN_22)
    ),
    "version 14, oversize options count landing on the token": _options_spanning_to(TOKEN_22),
}


def _save_root_holding(tmp_path: Path, blob: bytes) -> Path:
    """A save root whose one `.sav` holds exactly ``blob``."""
    save_root = make_save_root(tmp_path, FAKE_ACCOUNT_ID)
    (save_root / FAKE_ACCOUNT_ID / (SAVE_STEM + ".sav")).write_bytes(blob)
    return save_root


def test_discovery_blocklists_the_token_and_not_the_save_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A5, in process: the blocklist the gate builds from the real save root."""
    gate = load_gate()
    pin_save_root(monkeypatch, _save_root_with_named_unparseable_save(tmp_path), tmp_path)

    found = gate.discover_world_tokens(gate.Report())

    # Bound to scalars first, so a failure renders no list of values.
    token_listed = TOKEN_22 in found
    save_name_listed = SAVE_NAME_22 in found
    session_listed = SESSION_22 in found
    assert token_listed, "the identifier carried by the unparseable header was not recovered"
    assert not save_name_listed, "the save name became a world-token blocklist entry"
    # The MEASURED, ACCEPTED false positive: no fixed offset, so it is listed.
    assert session_listed, "the session name was dropped by a walk over a refused layout"


@pytest.mark.parametrize("label", sorted(LEAK_LAYOUTS))
def test_a_token_in_a_guessed_session_slot_is_still_blocklisted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, label: str
) -> None:
    """CS-1114: the refuted session-slot walk's three leaks, at the gate rung."""
    gate = load_gate()
    pin_save_root(monkeypatch, _save_root_holding(tmp_path, LEAK_LAYOUTS[label]), tmp_path)

    found = gate.discover_world_tokens(gate.Report())

    token_listed = TOKEN_22 in found
    assert token_listed, "LEAK: the token was not blocklisted - " + label


@pytest.mark.parametrize("wide", [False, True], ids=["narrow", "wide"])
def test_a_token_at_offset_12_behind_a_non_prologue_prefix_is_still_blocklisted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, wide: bool
) -> None:
    """CS-1114 residue 1: offset 12 alone is no evidence of a save name.

    All-zero leading bytes declare header version 0, which the parser refuses
    and which no layout reads a save name behind - so the value framed at
    offset 12 is exactly the unmeasured-layout identifier the scan exists for.
    """
    gate = load_gate()
    blob = bytes(12) + synthetic.fstring(TOKEN_22, wide=wide) + b"\x7f" * 8
    pin_save_root(monkeypatch, _save_root_holding(tmp_path, blob), tmp_path)

    found = gate.discover_world_tokens(gate.Report())

    token_listed = TOKEN_22 in found
    assert token_listed, "FAIL-OPEN: a token at offset 12 with no prologue was not blocklisted"


def test_a_staged_save_name_draws_no_diagnostic_while_the_token_does(tmp_path: Path) -> None:
    """A5, end to end, including the clause-7 no-echo half.

    NON-VACUOUS BY CONSTRUCTION: the token file's diagnostic proves the gate
    read the save, so the save-name file's silence is restraint, not blindness.
    """
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(_save_root_with_named_unparseable_save(tmp_path))
    name_target = write(tmp_path / "names-the-save.md", "saved as " + SAVE_NAME_22 + "\n")
    token_target = write(tmp_path / "names-the-token.md", "keyed by " + TOKEN_22 + "\n")

    result = run_gate(
        "--list-skipped", "--verbose", "--files", str(name_target), str(token_target), env=env
    )

    leaks = leak_diagnostics(result.stderr, "world token")
    token_reported = any(token_target.name in line for line in leaks)
    save_name_reported = any(name_target.name in line for line in leaks)
    assert token_reported, (
        "FAIL-OPEN: the recovered identifier drew no diagnostic\n" + result.stderr
    )
    assert not save_name_reported, (
        "a file holding only the save name was refused as a world-token leak\n" + result.stderr
    )
    for value in (SAVE_NAME_22, TOKEN_22):
        in_stdout = value in result.stdout
        in_stderr = value in result.stderr
        assert not in_stdout, "a scanned value was rendered on stdout"
        assert not in_stderr, "a scanned value was rendered on stderr"
