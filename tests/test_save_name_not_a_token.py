"""CS-1097 at the gate rung - a save name never becomes a blocklist entry.

The ROADMAP acceptance names this arm: a save name of exactly the measured
length must NOT become a blocklist entry while a real identifier in the same
buffer still does. It is graded on a REAL unparseable save written under a
temporary save root and a real gate process, never on a patched reader.

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

#: An INVENTED identifier carried by the same unparseable header.
TOKEN_22: Final = "Tkn9Gz" + "7Fc2Wv" + "4Qm8Ds" + "1Xh6"

#: The `.sav` basename. Shares no substring with either staged value, so a
#: block can only be attributed to the header scan and never to a world name.
SAVE_STEM: Final = "Quill" + "stone"

#: The header version no measured layout exists for.
UNPARSEABLE_VERSION: Final = 99


def _save_root_with_named_unparseable_save(tmp_path: Path) -> Path:
    """A save root whose one save refuses to parse and carries both values."""
    blob = synthetic.build_header(save_name=SAVE_NAME_22, world_token=TOKEN_22)
    blob = struct.pack("<i", UNPARSEABLE_VERSION) + blob[4:]
    blob += struct.pack("<I", synthetic.CHUNK_MAGIC)
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
    assert token_listed, "the identifier carried by the unparseable header was not recovered"
    assert not save_name_listed, "the save name became a world-token blocklist entry"


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
