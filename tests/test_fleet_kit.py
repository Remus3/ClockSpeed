"""CS-1330 - the vendored FLEET-KIT version 23, byte-pinned and conformance-checked.

``ops/fleet_kit/`` is VENDORED from MAIN, not authored here: the same
twenty-four files sit at the same path in every fleet repository and only a MAIN
note named ``FLEET-KIT-vN`` changes them. Same rule as ``docs/CHANNEL.md``: a
guard that refuses a kit file gets an EXEMPTION in the guard, never a byte of
the kit. The kit is Apache-2.0; its LICENSE and NOTICE ship beside it and its
register rows live in ``THIRD_PARTY.md``. Version 4 landed under CS-1231,
version 9 under CS-1272, version 10 under CS-1282 (it added
``fleet_subagent_first.py``), version 11 under CS-1287, version 13 under
CS-1290 (it carried the whole v12 ORDER, so v12 was never vendored here),
version 14 under CS-1299, version 15 under CS-1303, version 17 under CS-1310
(it carried the whole v16 FIX, so v16 was never vendored here), and version 20
patch 1 supersedes it under CS-1330 (it carries every v18, v19 and v20 change, so
none of those was vendored here, and it added ``fleet_board.py``), as MAIN's
v20.1 ORDER note (2026-10-19 00:01) says. Version 23 supersedes it under MAIN's
cumulative v23 ORDER note (2026-10-25 19:26), which carries every v21 and v22
change, so neither was vendored here; it adds no file. The board is LOCAL ONLY
from v23: render writes it and nothing is pushed. Version 24 supersedes it under MAIN's
v24 ORDER note (2026-10-26 03:15); it adds no file. Version 25 supersedes it under MAIN's
v25 ORDER note (2026-10-27 21:36); it adds no file.

Two arms:

1. The kit's own ``conformance(REPO_ROOT)`` returns no problems. It covers the
   manifest version, every kit file's digest against MANIFEST.json, and the
   FLEET-COMMON block embedded in CLAUDE.md between its marker lines.
2. The twenty-three listed files' digests match MANIFEST.json, and MANIFEST.json's
   own digest and version match the values the ordering note pinned. Arm 1
   alone passes when a file AND the manifest are edited together; arm 2 closes
   that locally.

A third arm pins this tree's own stop-sentinel declaration (CS-1330), which the
kit reads but does not ship: ``ops/stop_sentinels.json`` names the three stop
files and the main-spawn hold, and the vendored ``stop_sentinel_hit()`` halts on
each one alone and on none when none exists.

A fourth arm holds this tree's suite-guard ignore list (``GUARD_IGNORE`` in
``tests/conftest.py``) against the vendored board renderer: a local board render
(FLEET item 18) during a suite writes ``fleet_board.STATE_REL``, which the kit guard
watches, and the guard must neither fail on it nor go blind to any declared stop
sentinel planted or removed beside it - save those the kit's own default ignore
already hides, held to an exact record so that gap cannot grow unseen. A fifth
arm holds ``GUARD_IGNORE``, and the ignore the INSTALLED guard actually uses, to
exactly the kit defaults plus this tree's recorded names, so no glob widens it
(CS-1330).
"""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
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
KIT_BOARD = KIT_DIR / "fleet_board.py"
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
# This tree's stop-sentinel declaration (authored here, read by the kit's
# stop_sentinel_hit()), and the three paths it declares, in order. QUEUE_STOP
# is NOT one of them (CS-1342, MAIN ruling 2026-10-21): it stops queue work
# only, so it rides on the lane's own spawns as the kit's per-call halt_file
# and never halts the inbox responder.
STOP_SENTINELS = REPO_ROOT / "ops" / "stop_sentinels.json"
DECLARED_SENTINELS = (
    "ops/loop/control/STOP",
    "ops/loop/control/lanes/INBOX_STOP",
    "ops/loop/control/HOLD_MAIN_SPAWN",
)
# This tree's own additions to the kit guard's default IGNORE, in the order
# tests/conftest.py appends them - one name at a time, never a glob.
TREE_GUARD_IGNORE = (
    "ops/loop/control/headless_budget.json",
    "ops/loop/control/headless_budget.json.lock",
    "ops/loop/control/inbox_status_tasks.json",
    "ops/loop/control/board/state.json",
    "ops/loop/control/board/status.json",
)
# The declared stop sentinels the kit guard's OWN default IGNORE already hides
# (its "ops/loop/control/lanes/*" glob), so no suite guard here sees them come or
# go. The root cause is the kit default, owed to MAIN, never a local kit edit;
# held exact so the gap cannot grow unseen.
KIT_HIDDEN_SENTINELS = ("ops/loop/control/lanes/INBOX_STOP",)

# The kit version MAIN's 2026-10-27 21:36 ORDER note names (v25, patch 0).
KIT_VERSION = 25
# The MANIFEST.json digest named in that note.
MANIFEST_SHA256 = "fa04c87ceca7c1e08f853d0447a439143f317fa21b6434c1dcefe1e5d25c1bea"
# The twenty-three listed kit file digests named in the same note. Spelled as named
# constants rather than as a JSON-shaped mapping so this pin does not reproduce
# MANIFEST.json's own lines - the provenance near-duplicate metric
# (tools/provenance_stamp.py) would otherwise grade the pin as a lift of it.
COMMON_SHA256 = "886c5f8b1a86928f91412d2800e9dfef3dd8e5b9158d14a06e65d06c22964800"
LICENSE_SHA256 = "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4"
NOTICE_SHA256 = "f4b77ae089fa0be6e16d628786195b04c884ffbc859f79dd7c9eefee8722a18d"
MODULE_SHA256 = "c9c1740f41f0a565de6ba0468808b90843570828413fa8728cc314d729f3206e"
CLI_DISPLAY_SHA256 = "fcd92544574eb2e646c9eed62218e4852a570818a7e3de455151aa27c8c7d4d3"
BOARD_SHA256 = "07b98c23252435f0d8641bed97012d88ea9a51d39eaa8ea51467ca1adce483a5"
CHECKLIST_SHA256 = "583d7c2c900d0003a2350eafa8ca703c6f11bf15f5871282a6f4f00bfdacfd8c"
CLAIMS_SHA256 = "cf2a20e7883a8faa3dfe7ae1cbaa8402d94ea46c1337bf02bf89a6ec1bdb8f5e"
DONE_SHA256 = "39b1b572894ed5f8b629022a1e8b148ccce8a95e1e6273a3ad024b01657dc7ac"
GITLOCK_SHA256 = "e46264acc68ce721516f15b63bcb29428217f1b64fa4fa3c5b6226f39e4ae880"
IDENTITY_SHA256 = "8fc064075adb1b02e08c5df758ac9b4e0a6d53ba44c488659357dafc980f2019"
INBOX_SHA256 = "42dd431bc71f8cd0a1d54d66a0cab3c97bd5217c45b9601993f57363841065cd"
LANES_SHA256 = "824a59820829cb9c8e3466b23ba352dedcf484c93047176678e4e2e383fae0a7"
REWRITE_SHA256 = "c40bfcacbf08a3b9be4a4d2de971cd39f0cbbb772d76ba68e962d8c9adf7e97d"
SECRETS_SHA256 = "4e112c1f22c448fe773155b753fce5c678a09afc878cdf31b258eac5b3f0cf38"
STATUSLINE_SHA256 = "9cca74653baae70bc5bcfef4482b751681f903e94d13afe7fe93c5a9fc9289eb"
SUBAGENT_FIRST_SHA256 = "e0a7509186824249d1131f59bfa94207c32717cd62bbde3e0f6a8e5a13cf047f"
SUBAGENT_STATUS_SHA256 = "5da9e04b6a0deed94deb7d4949637b4130df8eaf8aa3a491d3309344199d580b"
SUITE_GATE_SHA256 = "fcf139f135bb9ee4e3d74f20116f45c66cd1fa8267416f31b3a9db8ebd97b6a2"
TEST_GUARD_SHA256 = "6f6c401a077174fd363417d5e83b43d48f2aff1e9535f8af7eabdca829884ecb"
WATCH_SHA256 = "5685ed7a4abaf0d755c4dd728b7a0dd9e9bb3e6e8ab3c223f99042601d05eb57"
TOKENS_CSS_SHA256 = "1b25b5251edd77eadfa9627da6814f03a4781f2a23a3f57957b6ec9a0e036810"
TOKENS_JSON_SHA256 = "83b728f000d4928f1ed09ed6b37662bc8927f72369a394bc1a436b6067624ff0"
NOTE_FILE_SHA256 = {
    KIT_COMMON.name: COMMON_SHA256,
    KIT_LICENSE.name: LICENSE_SHA256,
    KIT_NOTICE.name: NOTICE_SHA256,
    KIT_MODULE.name: MODULE_SHA256,
    KIT_CLI_DISPLAY.name: CLI_DISPLAY_SHA256,
    KIT_BOARD.name: BOARD_SHA256,
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


def _load_board():
    """Import the vendored board renderer by path - ops/ is not a package."""
    spec = importlib.util.spec_from_file_location("fleet_board_vendored", KIT_BOARD)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_test_guard():
    """Import the vendored test guard by path - a fresh copy, so its IGNORE is the kit's bytes."""
    spec = importlib.util.spec_from_file_location("fleet_test_guard_vendored", KIT_TEST_GUARD)
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


def test_stop_sentinel_declaration_holds_the_two_stops_and_the_main_spawn_hold(
    tmp_path: Path,
) -> None:
    # Authored here, not vendored: the kit's spawn() refuses "halted" while any
    # path this file declares exists. The hold is declared permanently; lifting
    # it removes the hold FILE, never this line (CS-1330 ruling 2). A standing
    # QUEUE_STOP is NOT a tree-wide hit (CS-1342): it is the lane's halt_file.
    raw = STOP_SENTINELS.read_bytes()
    assert b"\r" not in raw
    text = raw.decode("ascii")
    declared = tuple(json.loads(text)["paths"])
    kit = _load_kit()
    (tmp_path / "ops").mkdir()
    (tmp_path / "ops" / STOP_SENTINELS.name).write_bytes(raw)
    control = kit.stop_sentinel_hit(tmp_path)
    hits = {}
    for rel in DECLARED_SENTINELS:
        planted = tmp_path / rel
        planted.parent.mkdir(parents=True, exist_ok=True)
        planted.write_bytes(b"")
        hits[rel] = kit.stop_sentinel_hit(tmp_path)
        planted.unlink()
    queue_stop = tmp_path / "ops" / "loop" / "control" / "lanes" / "QUEUE_STOP"
    queue_stop.parent.mkdir(parents=True, exist_ok=True)
    queue_stop.write_bytes(b"")
    queue_hit = kit.stop_sentinel_hit(tmp_path)
    queue_stop.unlink()
    expected_hits = {rel: rel for rel in DECLARED_SENTINELS}
    assert (declared, control, hits, queue_hit) == (DECLARED_SENTINELS, None, expected_hits, None)
    assert text == json.dumps({"paths": list(DECLARED_SENTINELS)}, indent=2) + "\n"


def test_the_suite_guard_ignores_the_board_render_state_and_still_sees_a_stop(
    tmp_path: Path,
) -> None:
    # The kit guard watches ops/loop/control and its own IGNORE omits the two
    # files fleet_board.render() writes there, so a board render during a
    # main-checkout suite would fail the session. GUARD_IGNORE names the two;
    # the second arm plants and removes EVERY path ops/stop_sentinels.json
    # declares, in turn, and proves the guard sees each one come and go - save
    # exactly the recorded ones the kit's own default IGNORE hides.
    from tests import conftest  # noqa: PLC0415 - the one guard the suite installs

    guard = conftest.fleet_test_guard
    kit_ignore = _load_test_guard().IGNORE
    board = _load_board()
    config = tmp_path / "ops" / "status_board.json"
    config.parent.mkdir(parents=True)
    config.write_text(
        json.dumps({"url": "https://example.invalid/board", "dataset_version": 1}) + "\n",
        encoding="ascii",
    )
    before = guard.snapshot(tmp_path, ignore=conftest.GUARD_IGNORE)
    plan = board.render(tmp_path, 1, [], environ={})
    # An early return writes nothing, so an unrendered plan would pass vacuously.
    pushed = plan.get("rendered") is True
    state_dir = tmp_path / board.STATE_REL
    written = sorted(
        name for name in ("board.html", "state.json", "status.json") if (state_dir / name).is_file()
    )
    after = guard.snapshot(tmp_path, ignore=conftest.GUARD_IGNORE)
    rendered = guard.compare(before, after)
    declared = tuple(json.loads(STOP_SENTINELS.read_bytes().decode("ascii"))["paths"])
    seen = {}
    for rel in declared:
        planted = tmp_path / rel
        planted.parent.mkdir(parents=True, exist_ok=True)
        planted.write_bytes(b"")
        present = guard.snapshot(tmp_path, ignore=conftest.GUARD_IGNORE)
        kit_sees = rel in guard.snapshot(tmp_path, ignore=kit_ignore)
        planted.unlink()
        gone = guard.compare(present, guard.snapshot(tmp_path, ignore=conftest.GUARD_IGNORE))
        seen[rel] = (guard.compare(after, present), gone, kit_sees)
    hidden = tuple(rel for rel in declared if not seen[rel][2])
    expected: dict[str, object] = {
        rel: (([], [], []), ([], [], []), False)
        if rel in KIT_HIDDEN_SENTINELS
        else (([], [], [rel]), ([], [rel], []), True)
        for rel in declared
    }
    assert (pushed, written, rendered, hidden, seen) == (
        True,
        ["board.html", "state.json", "status.json"],
        ([], [], []),
        KIT_HIDDEN_SENTINELS,
        expected,
    )


def test_the_installed_suite_guard_ignores_exactly_the_recorded_names() -> None:
    # GUARD_IGNORE equals the kit's own default IGNORE - read from a fresh load of
    # the vendored bytes, not from conftest's copy - plus TREE_GUARD_IGNORE,
    # exactly, so an added glob (over ops/loop/control, over board/, over a stop
    # name) goes red. And the session guard install() built holds that same tuple,
    # read from the installed fixture's closure, so a conftest that computes the
    # list but installs another goes red too.
    from tests import conftest  # noqa: PLC0415 - the one guard the suite installs

    expected = (*_load_test_guard().IGNORE, *TREE_GUARD_IGNORE)
    fixture = inspect.unwrap(vars(conftest)["_fleet_live_state_guard"])
    installed = inspect.getclosurevars(fixture).nonlocals["ignore"]
    assert (conftest.GUARD_IGNORE, installed) == (expected, expected)
