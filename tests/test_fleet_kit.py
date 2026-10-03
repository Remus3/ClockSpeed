"""CS-1231 - the vendored FLEET-KIT version 4, byte-pinned and conformance-checked.

``ops/fleet_kit/`` is VENDORED from MAIN, not authored here: the same five
files sit at the same path in every fleet repository and only a MAIN note
named ``FLEET-KIT-vN`` changes them. Same rule as ``docs/CHANNEL.md``: a
guard that refuses a kit file gets an EXEMPTION in the guard, never a byte of
the kit. The kit is Apache-2.0; its LICENSE and NOTICE ship beside it and its
register rows live in ``THIRD_PARTY.md``.

Two arms:

1. The kit's own ``conformance(REPO_ROOT)`` returns no problems. It covers the
   manifest version, every kit file's digest against MANIFEST.json, and the
   FLEET-COMMON block embedded in CLAUDE.md between its marker lines.
2. The four listed files' digests match MANIFEST.json, and MANIFEST.json's own
   digest and version match the values the ordering note pinned. Arm 1 alone
   passes when a file AND the manifest are edited together; arm 2 closes that
   locally.
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

# The kit version MAIN's 2026-10-03 12:04 ORDER note names.
KIT_VERSION = 4
# The MANIFEST.json digest named in that note.
MANIFEST_SHA256 = "18c085e1fde34ff6cca2fa889ce404d0d37daeff59e261f55651e6fc493d1b07"
# The four listed kit file digests named in the same note. Spelled as named
# constants rather than as a JSON-shaped mapping so this pin does not reproduce
# MANIFEST.json's own lines - the provenance near-duplicate metric
# (tools/provenance_stamp.py) would otherwise grade the pin as a lift of it.
COMMON_SHA256 = "5f3385eef377fa127a5d5e5741acd302bb5bf9fc13e92fdc610bf3f0630f0f54"
LICENSE_SHA256 = "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4"
NOTICE_SHA256 = "9642ee05a624c33334c76a2f62c30d5370143bd7cb51e81f72c67b6d90d7ac07"
MODULE_SHA256 = "2a538bdd2c43cd8721ba5052f7f4e0a82921853c405b114dd1845866b3d73c7f"
NOTE_FILE_SHA256 = {
    KIT_COMMON.name: COMMON_SHA256,
    KIT_LICENSE.name: LICENSE_SHA256,
    KIT_NOTICE.name: NOTICE_SHA256,
    KIT_MODULE.name: MODULE_SHA256,
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
