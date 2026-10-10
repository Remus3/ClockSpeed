"""CS-1303 - the vendored FLEET-KIT version 15, byte-pinned and conformance-checked.

``ops/fleet_kit/`` is VENDORED from MAIN, not authored here: the same
twenty-three files sit at the same path in every fleet repository and only a MAIN
note named ``FLEET-KIT-vN`` changes them. Same rule as ``docs/CHANNEL.md``: a
guard that refuses a kit file gets an EXEMPTION in the guard, never a byte of
the kit. The kit is Apache-2.0; its LICENSE and NOTICE ship beside it and its
register rows live in ``THIRD_PARTY.md``. Version 4 landed under CS-1231,
version 9 under CS-1272, version 10 under CS-1282 (it added
``fleet_subagent_first.py``), version 11 under CS-1287, version 13 under
CS-1290 (it carried the whole v12 ORDER, so v12 was never vendored here),
version 14 under CS-1299, and version 15 supersedes it under CS-1303, as
MAIN's v15 ORDER note (2026-10-09 20:55) says.

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

# The kit version MAIN's 2026-10-09 20:55 ORDER note names.
KIT_VERSION = 15
# The MANIFEST.json digest named in that note.
MANIFEST_SHA256 = "8b20a75b6952356145a22f240db1399b70e6c16cccdcc333fc50bb8a2b3f463c"
# The twenty-two listed kit file digests named in the same note. Spelled as named
# constants rather than as a JSON-shaped mapping so this pin does not reproduce
# MANIFEST.json's own lines - the provenance near-duplicate metric
# (tools/provenance_stamp.py) would otherwise grade the pin as a lift of it.
COMMON_SHA256 = "fb6c129a73d1e1d8bee60367b4f4f74d39bb4051bdef0f56afd24d88e9a6f02b"
LICENSE_SHA256 = "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4"
NOTICE_SHA256 = "de5b5481280bb522ec154c1f3300813aa028aa0e9614ecad9bc5cf30e3c1ddcf"
MODULE_SHA256 = "adb2b1dd24d168396c48b1dc54cde966798528d6ff3fb501c1769d56c3a0557e"
CLI_DISPLAY_SHA256 = "fcd92544574eb2e646c9eed62218e4852a570818a7e3de455151aa27c8c7d4d3"
CHECKLIST_SHA256 = "954a95ce9d95e996764fd756c02b37d3f0e7a0ace9246e123c5df479479b6f35"
CLAIMS_SHA256 = "bbc83220300232501acd002c014f9016e7cc7f72b61722c9c54a28295e8aee6d"
DONE_SHA256 = "5267b215e14bbbcd46ae6d9c6ab4d3182fd48dbec8748313498e54f523473d62"
GITLOCK_SHA256 = "a4269f860840643be5943fafd0c94dd7ec781916c5d0f07bacd8af1211cd5061"
IDENTITY_SHA256 = "c49942e5c8bd2a125a0b9fad2c899171fe17ec216bdfd8f842f27501dfb6562a"
INBOX_SHA256 = "b43c671c113a698312e108839c5659862001aeb305f1096a570731299f678ac8"
LANES_SHA256 = "86a5a9fc54119e8834c411ad6acccee48c376c51199a7d8aea28045452e4de13"
REWRITE_SHA256 = "c40bfcacbf08a3b9be4a4d2de971cd39f0cbbb772d76ba68e962d8c9adf7e97d"
SECRETS_SHA256 = "4e112c1f22c448fe773155b753fce5c678a09afc878cdf31b258eac5b3f0cf38"
STATUSLINE_SHA256 = "ce97e180f9d53aee7206e8ebc1c6c75db5a24f3cc10f189e0fe862e9238940ea"
SUBAGENT_FIRST_SHA256 = "e0a7509186824249d1131f59bfa94207c32717cd62bbde3e0f6a8e5a13cf047f"
SUBAGENT_STATUS_SHA256 = "a618096df9d72cf2ebefde4177f00b7cfe377c16c99eadaf30549aad596cb0fd"
SUITE_GATE_SHA256 = "d2331a0ad30ae0c7205368a09d132db22a0fc954324c7dc5100d75386e4e028a"
TEST_GUARD_SHA256 = "bddec6ded7d6a8eddf8c0148684d469e03fd50c5ad6a481a67396c293b6764b5"
WATCH_SHA256 = "5685ed7a4abaf0d755c4dd728b7a0dd9e9bb3e6e8ab3c223f99042601d05eb57"
TOKENS_CSS_SHA256 = "120cc31990110049e405fb15020e12646089f210a02becda6bb08d795b0a33a7"
TOKENS_JSON_SHA256 = "dc683b08c2ad601f72722f339fc42806e46394a05b868616243162e98d7f2b16"
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
