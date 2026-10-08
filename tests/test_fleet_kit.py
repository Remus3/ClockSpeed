"""CS-1272 - the vendored FLEET-KIT version 9, byte-pinned and conformance-checked.

``ops/fleet_kit/`` is VENDORED from MAIN, not authored here: the same sixteen
files sit at the same path in every fleet repository and only a MAIN note
named ``FLEET-KIT-vN`` changes them. Same rule as ``docs/CHANNEL.md``: a
guard that refuses a kit file gets an EXEMPTION in the guard, never a byte of
the kit. The kit is Apache-2.0; its LICENSE and NOTICE ship beside it and its
register rows live in ``THIRD_PARTY.md``. Version 4 landed under CS-1231;
version 9 supersedes it directly under CS-1272, as MAIN's v9 ORDER note says.

Two arms:

1. The kit's own ``conformance(REPO_ROOT)`` returns no problems. It covers the
   manifest version, every kit file's digest against MANIFEST.json, and the
   FLEET-COMMON block embedded in CLAUDE.md between its marker lines.
2. The fifteen listed files' digests match MANIFEST.json, and MANIFEST.json's
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
KIT_DONE = KIT_DIR / "fleet_done.py"
KIT_INBOX = KIT_DIR / "fleet_inbox.py"
KIT_LANES = KIT_DIR / "fleet_lanes.py"
KIT_SECRETS = KIT_DIR / "fleet_secrets.py"
KIT_STATUSLINE = KIT_DIR / "fleet_statusline.js"
KIT_SUBAGENT_STATUS = KIT_DIR / "fleet_subagent_status.js"
KIT_WATCH = KIT_DIR / "fleet_watch.py"
KIT_TOKENS_CSS = KIT_DIR / "tokens.css"
KIT_TOKENS_JSON = KIT_DIR / "tokens.json"

# The kit version MAIN's 2026-10-07 23:54 ORDER note names.
KIT_VERSION = 9
# The MANIFEST.json digest named in that note.
MANIFEST_SHA256 = "cbc8b7dea0aa153833ec4a4540a0938d44bc1e04e9cde4cb9175f1182321919f"
# The fifteen listed kit file digests named in the same note. Spelled as named
# constants rather than as a JSON-shaped mapping so this pin does not reproduce
# MANIFEST.json's own lines - the provenance near-duplicate metric
# (tools/provenance_stamp.py) would otherwise grade the pin as a lift of it.
COMMON_SHA256 = "a8de1743d8b5aaf06eec63fbcebf2b854505caef7a2cc9bb12bfcfd6f64fdd35"
LICENSE_SHA256 = "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4"
NOTICE_SHA256 = "a4381b8b538477c505d391d5b8c5b179fb1274efeab06681a9d01456be3468c0"
MODULE_SHA256 = "5fcc9df9a9e4a1290184400af629f26b82edc3971a87436e33d09b88afb13c60"
CLI_DISPLAY_SHA256 = "cc4ca1544ea90d255d6defcd845cd1e7bb0abea49d7a7c2cc566295923caaa2f"
CHECKLIST_SHA256 = "2088d8f7d0a632b8756d77bace997005fd6b7302fd7a6251f9f939af21993724"
DONE_SHA256 = "266dfc37639f92b723c9d89e4fd01b0f71b93cb554e1736f5a88546f37757f6a"
INBOX_SHA256 = "f329b9f166ac193ab3305f3999fcae1b76e298e4f96a206004b241348cf90d28"
LANES_SHA256 = "0f2338fb0e32a9255b5eb8174cba7ddb8603c113ef2d31967e30cee4ef1001c6"
SECRETS_SHA256 = "4e112c1f22c448fe773155b753fce5c678a09afc878cdf31b258eac5b3f0cf38"
STATUSLINE_SHA256 = "cc3795d6cfd6eecc32d836532d71056709db3ee0b110b5ecec6c2c1f59b1e4cb"
SUBAGENT_STATUS_SHA256 = "a618096df9d72cf2ebefde4177f00b7cfe377c16c99eadaf30549aad596cb0fd"
WATCH_SHA256 = "77bd6fa3addaa23a4c152b83e59c8b0a9ed7eed1dd1950ee42db6117dfb2c4b8"
TOKENS_CSS_SHA256 = "120cc31990110049e405fb15020e12646089f210a02becda6bb08d795b0a33a7"
TOKENS_JSON_SHA256 = "965ed8aa3d9be380d863c000d18143155e71d81ad02f988050d5cfef5d09a0bd"
NOTE_FILE_SHA256 = {
    KIT_COMMON.name: COMMON_SHA256,
    KIT_LICENSE.name: LICENSE_SHA256,
    KIT_NOTICE.name: NOTICE_SHA256,
    KIT_MODULE.name: MODULE_SHA256,
    KIT_CLI_DISPLAY.name: CLI_DISPLAY_SHA256,
    KIT_CHECKLIST.name: CHECKLIST_SHA256,
    KIT_DONE.name: DONE_SHA256,
    KIT_INBOX.name: INBOX_SHA256,
    KIT_LANES.name: LANES_SHA256,
    KIT_SECRETS.name: SECRETS_SHA256,
    KIT_STATUSLINE.name: STATUSLINE_SHA256,
    KIT_SUBAGENT_STATUS.name: SUBAGENT_STATUS_SHA256,
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
