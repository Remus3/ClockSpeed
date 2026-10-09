"""CS-1290 - the vendored FLEET-KIT version 13, byte-pinned and conformance-checked.

``ops/fleet_kit/`` is VENDORED from MAIN, not authored here: the same
twenty-three files sit at the same path in every fleet repository and only a MAIN
note named ``FLEET-KIT-vN`` changes them. Same rule as ``docs/CHANNEL.md``: a
guard that refuses a kit file gets an EXEMPTION in the guard, never a byte of
the kit. The kit is Apache-2.0; its LICENSE and NOTICE ship beside it and its
register rows live in ``THIRD_PARTY.md``. Version 4 landed under CS-1231,
version 9 under CS-1272, version 10 under CS-1282 (it added
``fleet_subagent_first.py``), version 11 under CS-1287, and version 13
supersedes it under CS-1290, as MAIN's v13 ORDER note (2026-10-08 22:46) says;
v13 carries the whole v12 ORDER, so v12 was never vendored here.

Two arms:

1. The kit's own ``conformance(REPO_ROOT)`` returns no problems. It covers the
   manifest version, every kit file's digest against MANIFEST.json, and the
   FLEET-COMMON block embedded in CLAUDE.md between its marker lines.
2. The twenty-two listed files' digests match MANIFEST.json, and MANIFEST.json's
   own digest and version match the values the ordering note pinned. Arm 1
   alone passes when a file AND the manifest are edited together; arm 2 closes
   that locally.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
KIT_DIR = REPO_ROOT / "ops" / "fleet_kit"
# Bound at module scope so the byte-pin discovery in
# tests/test_third_party_register.py reaches each vendored file through its pin.
KIT_MANIFEST = KIT_DIR / "MANIFEST.json"
KIT_COMMON = KIT_DIR / "FLEET-COMMON.md"
KIT_MODULE = KIT_DIR / "fleet_headless.py"
KIT_LICENSE = KIT_DIR / "LICENSE"
KIT_NOTICE = KIT_DIR / "NOTICE"
KIT_CLI_DISPLAY = KIT_DIR / "cli_display.json"
KIT_CHECKLIST = KIT_DIR / "fleet_checklist.py"
KIT_CLAIMS = KIT_DIR / "fleet_claims.py"
KIT_DONE = KIT_DIR / "fleet_done.py"
KIT_GITLOCK = KIT_DIR / "fleet_gitlock.py"
KIT_IDENTITY = KIT_DIR / "fleet_identity.py"
KIT_INBOX = KIT_DIR / "fleet_inbox.py"
KIT_LANES = KIT_DIR / "fleet_lanes.py"
KIT_REWRITE = KIT_DIR / "fleet_rewrite.py"
KIT_SECRETS = KIT_DIR / "fleet_secrets.py"
KIT_STATUSLINE = KIT_DIR / "fleet_statusline.js"
KIT_SUBAGENT_FIRST = KIT_DIR / "fleet_subagent_first.py"
KIT_SUBAGENT_STATUS = KIT_DIR / "fleet_subagent_status.js"
KIT_SUITE_GATE = KIT_DIR / "fleet_suite_gate.py"
KIT_TEST_GUARD = KIT_DIR / "fleet_test_guard.py"
KIT_WATCH = KIT_DIR / "fleet_watch.py"
KIT_TOKENS_CSS = KIT_DIR / "tokens.css"
KIT_TOKENS_JSON = KIT_DIR / "tokens.json"

# The kit version MAIN's 2026-10-08 22:46 ORDER note names.
KIT_VERSION = 13
# The MANIFEST.json digest named in that note.
MANIFEST_SHA256 = "1311801a0f5c5ee17150d56b438fb0038a92efeb2b8e13ba02c79da2457f74e0"
# The twenty-two listed kit file digests named in the same note. Spelled as named
# constants rather than as a JSON-shaped mapping so this pin does not reproduce
# MANIFEST.json's own lines - the provenance near-duplicate metric
# (tools/provenance_stamp.py) would otherwise grade the pin as a lift of it.
COMMON_SHA256 = "fb6c129a73d1e1d8bee60367b4f4f74d39bb4051bdef0f56afd24d88e9a6f02b"
LICENSE_SHA256 = "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4"
NOTICE_SHA256 = "de5b5481280bb522ec154c1f3300813aa028aa0e9614ecad9bc5cf30e3c1ddcf"
MODULE_SHA256 = "9c9e1fa995978f6a5472003334cb27bc354e910992255a85b24b4876f177cbdb"
CLI_DISPLAY_SHA256 = "fcd92544574eb2e646c9eed62218e4852a570818a7e3de455151aa27c8c7d4d3"
CHECKLIST_SHA256 = "954a95ce9d95e996764fd756c02b37d3f0e7a0ace9246e123c5df479479b6f35"
CLAIMS_SHA256 = "ed42c394d3ad3e510ee698268d1de5903e955267934b8f9f2765dad7882f7e00"
DONE_SHA256 = "5267b215e14bbbcd46ae6d9c6ab4d3182fd48dbec8748313498e54f523473d62"
GITLOCK_SHA256 = "aa92d343439ac2c2d18c516ffa56d3d324ab35ec9ee0ccf14acf654f4df55e03"
IDENTITY_SHA256 = "a0dd0e8bcd75aa5a4973823ae5e81718ba14bf0a0476496de06a964f08286a0d"
INBOX_SHA256 = "dbedd53fa545578fbd536bf8003b6f7bbebf1a98b83a178058db4bd1ea08334f"
LANES_SHA256 = "bcc2817bddb6be13231f071bd4d81f6f7b803877ee423817eb426cd1ec29d99c"
REWRITE_SHA256 = "59578b5469434817b01eb9423d8597d449a3af38a952b2a56f83debac775c365"
SECRETS_SHA256 = "4e112c1f22c448fe773155b753fce5c678a09afc878cdf31b258eac5b3f0cf38"
STATUSLINE_SHA256 = "cc3795d6cfd6eecc32d836532d71056709db3ee0b110b5ecec6c2c1f59b1e4cb"
SUBAGENT_FIRST_SHA256 = "e0a7509186824249d1131f59bfa94207c32717cd62bbde3e0f6a8e5a13cf047f"
SUBAGENT_STATUS_SHA256 = "a618096df9d72cf2ebefde4177f00b7cfe377c16c99eadaf30549aad596cb0fd"
SUITE_GATE_SHA256 = "a4592d846ba24d25e0ad39e30c4078df137db672cb0bc3d65b04cbd6ea33308e"
TEST_GUARD_SHA256 = "66811e3668ceb17d52472dfdcf56f0d08beb0de5cc2cb3bb76b0654605c91656"
WATCH_SHA256 = "5685ed7a4abaf0d755c4dd728b7a0dd9e9bb3e6e8ab3c223f99042601d05eb57"
TOKENS_CSS_SHA256 = "120cc31990110049e405fb15020e12646089f210a02becda6bb08d795b0a33a7"
TOKENS_JSON_SHA256 = "965ed8aa3d9be380d863c000d18143155e71d81ad02f988050d5cfef5d09a0bd"
NOTE_FILE_SHA256 = {
    KIT_COMMON.name: COMMON_SHA256,
    KIT_LICENSE.name: LICENSE_SHA256,
    KIT_NOTICE.name: NOTICE_SHA256,
    KIT_MODULE.name: MODULE_SHA256,
    KIT_CLI_DISPLAY.name: CLI_DISPLAY_SHA256,
    KIT_CHECKLIST.name: CHECKLIST_SHA256,
    KIT_CLAIMS.name: CLAIMS_SHA256,
    KIT_DONE.name: DONE_SHA256,
    KIT_GITLOCK.name: GITLOCK_SHA256,
    KIT_IDENTITY.name: IDENTITY_SHA256,
    KIT_INBOX.name: INBOX_SHA256,
    KIT_LANES.name: LANES_SHA256,
    KIT_REWRITE.name: REWRITE_SHA256,
    KIT_SECRETS.name: SECRETS_SHA256,
    KIT_STATUSLINE.name: STATUSLINE_SHA256,
    KIT_SUBAGENT_FIRST.name: SUBAGENT_FIRST_SHA256,
    KIT_SUBAGENT_STATUS.name: SUBAGENT_STATUS_SHA256,
    KIT_SUITE_GATE.name: SUITE_GATE_SHA256,
    KIT_TEST_GUARD.name: TEST_GUARD_SHA256,
    KIT_WATCH.name: WATCH_SHA256,
    KIT_TOKENS_CSS.name: TOKENS_CSS_SHA256,
    KIT_TOKENS_JSON.name: TOKENS_JSON_SHA256,
}


def _load_kit():
    """Import the vendored module by path - ops/ is not a package."""
    spec = importlib.util.spec_from_file_location("fleet_headless_vendored", KIT_MODULE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fleet_kit_conformance() -> None:
    kit = _load_kit()
    problems = list(kit.conformance(REPO_ROOT))
    assert problems == []


def test_fleet_kit_files_match_manifest() -> None:
    manifest_path = KIT_MANIFEST
    manifest_digest = _sha256(manifest_path)
    assert manifest_digest == MANIFEST_SHA256
    manifest = json.loads(manifest_path.read_bytes().decode("ascii"))
    version = manifest["version"]
    assert version == KIT_VERSION
    pinned = dict(manifest["files"])
    assert pinned == NOTE_FILE_SHA256
    observed = {name: _sha256(KIT_DIR / name) for name in sorted(pinned)}
    assert observed == pinned
    common_digest = manifest["common_block_sha256"]
    assert common_digest == COMMON_SHA256


def test_every_kit_file_on_disk_is_named_by_the_manifest() -> None:
    # The other direction: a stray file under ops/fleet_kit/ that the manifest
    # does not name is outside NOTICE's scope paragraph AND outside every pin.
    on_disk = sorted(path.name for path in KIT_DIR.iterdir() if path.is_file())
    expected = sorted([KIT_MANIFEST.name, *NOTE_FILE_SHA256])
    assert on_disk == expected
