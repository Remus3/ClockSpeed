"""Tests for the version-pin guard (h) and the work-item guard (i).

THE CRITERION GUARD (h) GRADES, verbatim from ROADMAP.md CS-200: "the drift
guard goes red when the pin is manually corrupted and green after re-extract".
``test_a_corrupted_pin_goes_red_and_a_regenerated_pin_goes_green_again`` is
that transcript, and it asserts the process EXIT CODE at every step rather
than only the status string - the exit code is what CI reads.

THE CONSTRAINT THAT SHAPES EVERY TEST HERE. `.github/workflows/tier1.yml` runs
`python tools/drift_guard.py` on ubuntu-latest, a runner with no game install.
A guard that failed on a missing install would turn the lane that must never
be red red on every push, so an unresolvable install is never a FAIL - it is a
non-failing status plus an explicit skip record, and
``test_an_unresolvable_install_never_fails_and_exits_zero`` is the test that
protects that lane.

Every install in this module is fabricated in tmp_path out of synthetic
material, so the live-comparison half of the guard is exercised on a machine
that has never had the game on it. Nothing here reads the real install, the
real save directory or the operator's local configuration - the resolver is
pointed at a path under tmp_path in every test through the environment
override that `clockspeed/data/locate.py` publishes.

THE CRITERION GUARD (i) GRADES, verbatim from ROADMAP.md CS-211: a guard that
"fails when any `CS-nnn` appears as an OPEN entry in `ROADMAP.md` while also
carrying a closure heading in `docs/LEDGER.md`", and when any ID is recorded in
more than one owner file, "with a control proving the guard fires on a planted
duplicate rather than passing on an empty scan".

THE TWO HALVES ARE GRADED ON DIFFERENT MATERIAL, ON PURPOSE. The FIRING half
runs on synthetic owner files built under tmp_path: a plant has to be planted,
and planting into the tracked ROADMAP.md or docs/LEDGER.md would mean a test
that edits the repository it is measuring. The GREEN half runs on the REAL
tree, because the failure it protects against is a guard red on correct history
- an ID legitimately reaches `docs/LEDGER.md` before it closes, since CLAUDE.md
section 6 requires a frozen-file grant to be recorded BEFORE the edit - and a
fixture proves nothing about the file the operator actually reads.

WHY THE REAL-TREE CONTROLS DERIVE THEIR OWN SETS rather than listing the IDs
they were written for. A list of IDs is stale as soon as one of them closes,
and a green about a stale list is a green about nothing. Each control below
derives its population from the tree with its own patterns - not by importing
the guard's, because two derivations from one regex agree by construction - and
asserts that population is non-empty before asserting anything about it.

WHY THE SYNTHETIC OWNER FILES ARE NOT NAMED AFTER THE REAL ONES. The same
hazard, one level up: the fixture's doctrine sentence declares owner files this
repository has never had, so a guard that BELIEVED a four-entry map instead of
parsing one cannot read the fixture at all. When the fixture restated the real
four paths verbatim, a hardcoded map and a parse agreed by construction and no
test in this module could tell them apart. Synthetic ids stay in the CS-9nn and
CS-G9n blocks, which the phase items - CS-0nn through CS-7nn - cannot reach, so
a stray fixture string can never be mistaken for a real item in a grep.
"""

from __future__ import annotations

import contextlib
import errno
import fnmatch
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator
from pathlib import Path
from types import MappingProxyType, ModuleType
from typing import Any, Final

import pytest

from clockspeed.data.locate import (
    ENV_ACCOUNT_DIR,
    ENV_GAME_DIR,
    ENV_LOCAL_CONFIG,
    ENV_SAVE_ROOT,
    MIN_ACCOUNT_ID_DIGITS,
)
from clockspeed.data.version import DOCS_RELATIVE_PARTS, build_pin, extract_pin_block, write_pin

REPO_ROOT = Path(__file__).resolve().parents[2]
DRIFT_GUARD_SOURCE = REPO_ROOT / "tools" / "drift_guard.py"
VERSION_SOURCE = REPO_ROOT / "clockspeed" / "data" / "version.py"

GUARD_ID = "h"
SYNTHETIC_BUILD = "++SyntheticGame+rel-test-CL-1"

# A run of digits long enough to be an account id. Derived from the resolver's
# own floor rather than restated, so the two cannot drift apart.
_ACCOUNT_ID_SHAPE = re.compile(r"(?<![0-9A-Za-z])[0-9]{" + str(MIN_ACCOUNT_ID_DIGITS) + r",}")

# The filename an injected OSError claims to have failed on. Distinctive
# enough that finding it anywhere in guard output is unambiguous, and
# synthetic, so the assertion that hunts it never has to handle a real path.
INJECTED_FILENAME = "ZZ-SYNTHETIC-OPERATOR-PATH-ZZ"


def unreadable(*_args: object, **_kwargs: object) -> Any:
    """Raise the OSError a Windows filesystem raises, filename and all.

    ``str()`` on this exception renders as "[Errno 13] Permission denied:
    'ZZ-...'" while ``strerror`` renders as "Permission denied". That gap is
    the whole defect class: an f-string interpolating the exception publishes
    the path the failure happened on, and CLAUDE.md non-negotiable 12 counts
    an error message as an echo path exactly like a debug dump.

    Raises:
        OSError: Always.
    """
    raise OSError(errno.EACCES, "Permission denied", INJECTED_FILENAME)


def assert_reported_without_the_filename(rendered: str) -> None:
    """Assert an error path named the REASON and not the path it failed on.

    Both halves are required. Without the second, blanking the message
    entirely would pass - and a guard that reports nothing when it cannot read
    a file is a worse bug than the one being fixed, because it is silent.

    Args:
        rendered: Everything the guard emitted for the failure.
    """
    leaked = INJECTED_FILENAME in rendered
    assert not leaked, "an OSError message carried the filename it failed on"
    assert "Permission denied" in rendered, (
        "the reason vanished along with the filename, so the guard now fails silently"
    )


def personal_data_needles() -> set[str]:
    """Strings that must never reach guard output, derived independently.

    THIS IS THE ORACLE, AND IT MUST NOT BE THE CODE UNDER TEST. The previous
    version of the privacy test below asked ``redact(rendered) != rendered``,
    which reads like a test for "the output holds personal data" and is not
    one: it reports only what the redactor already recognises, so a redactor
    with a blind spot certifies as clean exactly the strings it cannot see
    (CONVENTIONS.md section 15.1). That was not theoretical here. Every repo
    in this module is built under ``tmp_path``, which sits under the temp
    directory, which Windows hands back in 8.3 short form - a rendering the
    redactor did not know, so the oracle answered "clean" about a string that
    was the operator's home directory.

    Everything below is read from the environment and the filesystem directly.
    Nothing comes from clockspeed.data.locate.

    Returns:
        The distinct non-empty needles, including the account-name segment of
        the home directory in both the long and the 8.3 rendering.
    """
    found = {
        os.environ.get("USERPROFILE") or "",
        os.environ.get("LOCALAPPDATA") or "",
        os.environ.get("APPDATA") or "",
        os.environ.get("USERNAME") or "",
        os.environ.get("USER") or "",
        os.environ.get("COMPUTERNAME") or "",
        tempfile.gettempdir(),
    }
    try:
        home = Path.home()
    except (OSError, RuntimeError):
        return {value for value in found if value}
    found.add(str(home))
    found.add(home.name)
    depth = len(home.parts)
    temporary = Path(tempfile.gettempdir()).parts
    if len(temporary) >= depth and temporary[: depth - 1] == home.parts[: depth - 1]:
        found.add(temporary[depth - 1])
    return {value for value in found if value}


def _load_drift_guard() -> ModuleType:
    """Load tools/drift_guard.py by path.

    tools/ is not an importable package - it is a directory of entry-point
    scripts - so the module is loaded from its file the same way the guard
    itself loads tools/doc_budget.py.

    Returns:
        The loaded module.
    """
    spec = importlib.util.spec_from_file_location("clockspeed_drift_guard", DRIFT_GUARD_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {DRIFT_GUARD_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


drift_guard = _load_drift_guard()


# ---------------------------------------------------------------------------
# A repository the guard can be pointed at
# ---------------------------------------------------------------------------

_CLAUDE_MD = """# Fake repository for the drift guard tests

## 6. Frozen files

- `LICENSE`
"""

_CONVENTIONS_MD = """# Fake conventions

## 2. Documentation topology and single source of truth

| File | Owns |
|---|---|
| `CLAUDE.md` | Rules |

## 3. Something else
"""

_MEMORY_MD = """# Memory index

No leaves yet.
"""

_PORTS_JSON = {
    "base": 41000,
    "band": {"start": 41000, "end": 41000},
    "allocations": {"41000": "fake dashboard"},
    "reserved": [],
}

# The item-notes family guard (j) grades, and the tier 1 lane guard (k) grades.
# Spelled here rather than imported from the guard, so a moved path is a red
# fixture instead of a fixture that follows the guard wherever it goes.
ROADMAP_RELATIVE = "ROADMAP.md"
ITEM_NOTES_INDEX_RELATIVE = "docs/item_notes.md"
ITEM_NOTES_LEAF_RELATIVE = "docs/item_notes/phase7.md"
TIER1_WORKFLOW_RELATIVE = ".github/workflows/tier1.yml"
# CS-1115 - a budgeted file guard (a) must measure. Guard (a) now reports an
# absent one as could-not-look, so the base tree has to carry it.
UPSTREAM_WATCH_RELATIVE = "docs/upstream_watch.md"

_ITEM_NOTES_ROADMAP = """# Fake roadmap for the drift guard tests

## Phase 7 - a synthetic phase

CS-904 - a synthetic routed item - acceptance: none - tier: 1 - detail: `docs/item_notes.md`
"""

# CS-1112 - the index carries the leaf table and NO routing row; CS-904 is
# routed by its ROADMAP.md detail field through the one-row rule below.
_ITEM_NOTES_INDEX = """# Fake item-notes index

## Which leaf an item lands in

| Leaf | Holds |
|---|---|
| `docs/item_notes/phase7.md` | ROADMAP `Phase 7` |
"""

_ITEM_NOTES_LEAF = """# Fake item-notes leaf

## CS-904

Synthetic detail.
"""


def make_repo(root: Path, *, with_pin: bool = True) -> Path:
    """Build the smallest tree EVERY drift guard reports PASS on.

    Guards (a) through (g) each need something in the tree, and any one of them
    failing would make an exit-code assertion about guard (h) meaningless. So
    the tree carries a budgeted CLAUDE.md with a frozen-file section, a
    CONVENTIONS section 2 ownership table naming one file that exists, a memory
    index with no leaves, and a fully covered port band.

    CS-1113 - AND GUARDS (i), (j) AND (k) PASS TOO, NOT WARN. A WARN meaning
    "could not look" now makes the overall result UNGRADED and the exit code
    non-zero, so a tree that left those three unread would be red before any
    plant and every exit-code transcript below would prove nothing. The tree
    therefore also carries the synthetic work-item doctrine and owner files, a
    one-item item-notes family routed from a synthetic ROADMAP.md, and a copy of
    the real tier 1 workflow - copied, like the pin, because guard (k) pins its
    levels to the recorded values and a hand-written lane would restate them.

    CS-1115 - AND EVERY BUDGETED FILE GUARD (a) MUST MEASURE. An absent one is a
    size never measured, so it is could-not-look too; the tree carries a small
    docs/upstream_watch.md for that reason alone.

    Args:
        root: Directory to build in.
        with_pin: Whether to place a copy of the real version module, pin and
            all. False leaves the pin absent, which is a distinct case.

    Returns:
        ``root``, for chaining.
    """
    root.mkdir(parents=True, exist_ok=True)
    (root / "CLAUDE.md").write_text(_CLAUDE_MD, encoding="utf-8")
    (root / "CONVENTIONS.md").write_text(_CONVENTIONS_MD, encoding="utf-8")
    memory = root / "memory"
    memory.mkdir(parents=True, exist_ok=True)
    (memory / "MEMORY.md").write_text(_MEMORY_MD, encoding="utf-8")
    config = root / "config"
    config.mkdir(parents=True, exist_ok=True)
    (config / "ports.json").write_text(json.dumps(_PORTS_JSON, indent=2), encoding="utf-8")
    if with_pin:
        target = pin_path(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(VERSION_SOURCE, target)
    (root / "CLAUDE.md").write_text(_WORK_ITEM_CLAUDE_MD, encoding="utf-8")
    for state, body in (
        ("OPEN", _WORK_ITEM_OPEN),
        ("ASPIRATIONAL", _WORK_ITEM_ASPIRATIONAL),
        ("GATED", _WORK_ITEM_GATED),
        ("CLOSED", _WORK_ITEM_CLOSED),
    ):
        path = root / WORK_ITEM_OWNERS[state]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    (root / ROADMAP_RELATIVE).write_text(_ITEM_NOTES_ROADMAP, encoding="utf-8")
    leaf = root / ITEM_NOTES_LEAF_RELATIVE
    leaf.parent.mkdir(parents=True, exist_ok=True)
    leaf.write_text(_ITEM_NOTES_LEAF, encoding="utf-8")
    (root / ITEM_NOTES_INDEX_RELATIVE).write_text(_ITEM_NOTES_INDEX, encoding="utf-8")
    workflow = root / TIER1_WORKFLOW_RELATIVE
    workflow.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REPO_ROOT / TIER1_WORKFLOW_RELATIVE, workflow)
    (root / UPSTREAM_WATCH_RELATIVE).write_text("# Fake upstream watch list\n", encoding="utf-8")
    return root


@contextlib.contextmanager
def refused(path: Path) -> Iterator[None]:
    """Hold a REAL operating-system read fault on a file or a directory.

    CS-1115, following CS-1104's ``_unlistable``. On Windows an EXCLUSIVE handle
    (share mode zero) on the path itself, so a read or a listing meets a real
    sharing violation while a stat still answers. MEASURED there: a deny ACE
    did NOT stop this elevated account, so it is not used. Elsewhere a mode of
    zero, with a control that the bits really cleared. No stub - the whole read
    path meets the fault.

    SKIPPED ONLY where no fault can be manufactured: a POSIX account the mode
    does not bind (root reads a mode-zero file). The skip reason says so, and
    the Windows branch never skips.

    Args:
        path: The file or directory to refuse.

    Yields:
        None, while the fault holds.
    """
    if os.name == "nt":
        import ctypes  # noqa: PLC0415 - Windows-only
        from ctypes import wintypes  # noqa: PLC0415 - Windows-only

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateFileW.restype = wintypes.HANDLE
        kernel32.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        generic_read, no_sharing, open_existing = 0x80000000, 0, 3
        normal, backup_semantics = 0x80, 0x02000000
        flags = backup_semantics if path.is_dir() else normal
        handle = kernel32.CreateFileW(
            str(path), generic_read, no_sharing, None, open_existing, flags, None
        )
        assert handle not in (None, wintypes.HANDLE(-1).value), "control: no exclusive handle"
        try:
            yield
        finally:
            kernel32.CloseHandle(handle)
        return
    mode = path.stat().st_mode
    path.chmod(0)
    landed = path.stat().st_mode & 0o777
    try:
        if path.is_dir():
            list(path.iterdir())
        else:
            path.read_bytes()
    except PermissionError:
        binds = True
    else:
        binds = False
    if landed or not binds:
        path.chmod(mode)
    assert not landed, "control: the mode did not drop to zero"
    if not binds:
        euid = getattr(os, "geteuid", lambda: "unknown")()
        pytest.skip(f"a mode of zero does not refuse a read to euid {euid}")
    try:
        yield
    finally:
        path.chmod(mode)


def pin_path(root: Path) -> Path:
    """Return where the guard reads the pin from inside ``root``.

    Args:
        root: The repository root.

    Returns:
        The version module path.
    """
    return root / "clockspeed" / "data" / "version.py"


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A fake repository with the guard pointed at it and no install resolvable.

    Args:
        tmp_path: pytest temporary directory.
        monkeypatch: pytest monkeypatch fixture.

    Returns:
        The fake repository root.
    """
    root = make_repo(tmp_path / "repo")
    monkeypatch.setattr(drift_guard, "repo_root", lambda: root)
    no_install(monkeypatch, tmp_path)
    return root


def no_install(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Point every resolver at a path under tmp_path that does not exist.

    An override naming a missing directory resolves to None rather than falling
    through to auto-detection, so this makes the outcome identical on a machine
    with the game installed and on one without.

    Args:
        monkeypatch: pytest monkeypatch fixture.
        tmp_path: pytest temporary directory.
    """
    for name in (ENV_GAME_DIR, ENV_SAVE_ROOT, ENV_ACCOUNT_DIR, ENV_LOCAL_CONFIG):
        monkeypatch.setenv(name, str(tmp_path / "absent" / name.lower()))


def fake_install(root: Path, raw: bytes) -> Path:
    """Write a synthetic docs file into a fabricated install directory.

    Args:
        root: Directory to build the install in.
        raw: The synthetic docs bytes.

    Returns:
        The install root.
    """
    docs = root.joinpath(*DOCS_RELATIVE_PARTS)
    docs.parent.mkdir(parents=True, exist_ok=True)
    docs.write_bytes(raw)
    return root


def synthetic_docs(extra_recipes: int = 0) -> bytes:
    """Encode a small synthetic docs document.

    Args:
        extra_recipes: Extra recipe entries, so two documents can be made to
            differ in a way the census reports.

    Returns:
        Encoded document bytes, UTF-16 with a byte-order mark.
    """
    recipes = [{"ClassName": f"Recipe_Synth{index}_C"} for index in range(2 + extra_recipes)]
    groups = [
        {
            "NativeClass": "/Script/CoreUObject.Class'/Script/FactoryGame.FGRecipe'",
            "Classes": recipes,
        },
        {
            "NativeClass": "/Script/CoreUObject.Class'/Script/FactoryGame.FGPowerShardDescriptor'",
            "Classes": [
                {
                    "ClassName": "Desc_SynthOverclockShard_C",
                    "mPowerShardType": "PST_Overclock",
                    "mExtraPotential": "0.500000",
                }
            ],
        },
    ]
    return json.dumps(groups).encode("utf-16")


def run_main(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, dict[str, Any]]:
    """Run the guard driver end to end and read back its machine-readable report.

    Args:
        capsys: pytest capture fixture.
        *args: Extra command-line arguments.

    Returns:
        (process exit code, the parsed JSON report).
    """
    code = drift_guard.main(["--json", *args])
    payload = json.loads(capsys.readouterr().out)
    return code, payload


def guard_of(report: dict[str, Any], guard_id: str = GUARD_ID) -> dict[str, Any]:
    """Pull one guard's record out of a report.

    Args:
        report: The parsed JSON report.
        guard_id: Which guard.

    Returns:
        The guard record.
    """
    matches: list[dict[str, Any]] = [guard for guard in report["guards"] if guard["id"] == guard_id]
    assert len(matches) == 1, f"expected exactly one guard {guard_id!r}, found {len(matches)}"
    return matches[0]


def corrupt_pin(path: Path) -> str:
    """Hand-edit one census number in a pin, the way an operator would.

    Args:
        path: The version module to corrupt.

    Returns:
        The value that was written, for an assertion that names it.

    Raises:
        AssertionError: The edit did not apply. A mutation that fails to apply
            looks GREEN (CONVENTIONS.md section 7.2), so this refuses to return
            a corruption it did not make.
    """
    source = path.read_text(encoding="utf-8")
    pattern = re.compile(r'("entry_count": )(\d+)')
    match = pattern.search(source)
    assert match is not None, "no entry_count in the pin - this edit would corrupt nothing"
    replacement = str(int(match.group(2)) + 1)
    corrupted = pattern.sub(rf"\g<1>{replacement}", source, count=1)
    assert corrupted != source, "the corruption did not apply"
    path.write_text(corrupted, encoding="utf-8", newline="\n")
    return replacement


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_the_version_pin_guard_is_registered_and_reported(repo: Path) -> None:
    guards, _skips, _source = drift_guard.run_all(repo)
    ids = [guard["id"] for guard in guards]
    assert GUARD_ID in ids
    assert ids == sorted(ids), "guards are reported in id order"
    assert "pin" in guard_of({"guards": guards})["name"].lower()


# ---------------------------------------------------------------------------
# The CS-200 transcript: red when corrupted, green after re-extract
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("repo")
def test_a_well_formed_pin_is_green_with_no_install(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, report = run_main(capsys)
    assert guard_of(report)["status"] == "PASS"
    assert code == 0


def test_a_corrupted_pin_goes_red_and_a_regenerated_pin_goes_green_again(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, report = run_main(capsys)
    assert (guard_of(report)["status"], code) == ("PASS", 0)

    corrupt_pin(pin_path(repo))
    code, report = run_main(capsys)
    guard = guard_of(report)
    assert guard["status"] == "FAIL"
    assert code != 0, "a corrupted pin must be a non-zero exit code, not only a red word"
    assert report["verdict"] == "DRIFT"
    assert GUARD_ID in report["drift"]
    assert any("integrity" in line.lower() for line in guard["detail"])
    assert any("--re-extract" in line for line in guard["detail"])

    write_pin(pin_path(repo), build_pin(synthetic_docs(), SYNTHETIC_BUILD))
    code, report = run_main(capsys)
    assert guard_of(report)["status"] == "PASS"
    assert code == 0


def test_a_pin_with_its_integrity_field_stripped_is_red(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = pin_path(repo)
    payload = extract_pin_block(path.read_text(encoding="utf-8"))
    del payload["integrity"]
    write_pin(path, payload)

    code, report = run_main(capsys)
    assert guard_of(report)["status"] == "FAIL"
    assert code != 0


def test_a_pin_whose_block_is_not_json_is_red(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = pin_path(repo)
    source = path.read_text(encoding="utf-8")
    anchor = '_PIN_JSON: Final = """\n{'
    assert anchor in source, "the anchor moved - this test would mutate nothing"
    broken = source.replace(anchor, anchor + ",", 1)
    assert broken != source, "the mutation did not apply"
    path.write_text(broken, encoding="utf-8", newline="\n")

    code, report = run_main(capsys)
    assert guard_of(report)["status"] == "FAIL"
    assert code != 0


# ---------------------------------------------------------------------------
# The tier-1 lane: no install must never be a failure
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("repo")
def test_an_unresolvable_install_never_fails_and_exits_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, report = run_main(capsys)
    guard = guard_of(report)
    assert guard["status"] != "FAIL"
    assert code == 0
    assert any(
        "install" in skip["reason"].lower() and "unresolved" in skip["reason"].lower()
        for skip in report["skipped"]
    ), "an install that was never looked at must be recorded in the skip list"
    assert any("internal integrity" in line.lower() for line in guard["detail"])


def test_an_absent_pin_warns_rather_than_failing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_repo(tmp_path / "repo", with_pin=False)
    monkeypatch.setattr(drift_guard, "repo_root", lambda: root)
    no_install(monkeypatch, tmp_path)

    code, report = run_main(capsys)
    assert guard_of(report)["status"] == "WARN"
    # CS-1113 - an absent pin is a pin nobody checked, so the run is UNGRADED:
    # never DRIFT, and never CLEAN.
    assert report["verdict"] == "UNGRADED"
    assert code != 0
    assert any("version.py" in skip["path"] for skip in report["skipped"])


# ---------------------------------------------------------------------------
# The live half, against a fabricated install
# ---------------------------------------------------------------------------


def test_a_live_docs_file_matching_the_pin_stays_green(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    raw = synthetic_docs()
    install = fake_install(tmp_path / "install", raw)
    monkeypatch.setenv(ENV_GAME_DIR, str(install))
    write_pin(pin_path(repo), build_pin(raw, SYNTHETIC_BUILD))

    code, report = run_main(capsys)
    guard = guard_of(report)
    assert guard["status"] == "PASS"
    assert code == 0
    assert any("matches" in line.lower() for line in guard["detail"])


def test_a_live_docs_file_that_moved_turns_the_guard_red(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    install = fake_install(tmp_path / "install", synthetic_docs(extra_recipes=3))
    monkeypatch.setenv(ENV_GAME_DIR, str(install))
    write_pin(pin_path(repo), build_pin(synthetic_docs(), SYNTHETIC_BUILD))

    code, report = run_main(capsys)
    guard = guard_of(report)
    assert guard["status"] == "FAIL"
    assert code != 0
    assert any("sha256" in line.lower() for line in guard["detail"])
    assert any("FGRecipe" in line for line in guard["detail"]), (
        "a live mismatch must name what moved, not merely that something did"
    )


@pytest.mark.usefixtures("repo")
def test_a_missing_docs_file_under_a_resolved_install_never_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    hollow = tmp_path / "hollow-install"
    hollow.mkdir()
    monkeypatch.setenv(ENV_GAME_DIR, str(hollow))

    code, report = run_main(capsys)
    assert guard_of(report)["status"] != "FAIL"
    assert code == 0


# ---------------------------------------------------------------------------
# Privacy
# ---------------------------------------------------------------------------


def test_the_personal_data_oracle_actually_detects() -> None:
    """The oracle finds a home path, and is not merely empty.

    An empty needle set makes the test below permanently green while proving
    nothing - a claim about the pattern rather than about the code
    (CONVENTIONS.md section 15.1), which is the same failure mode as the
    redact()-as-its-own-oracle it replaced. Both directions are pinned here:
    the needles exist, and a string built out of a real home path trips them.

    Nothing is printed. The sample is constructed and consumed inside this
    function, and only counts cross the assertion boundary.
    """
    needles = personal_data_needles()
    needle_count = len(needles)
    assert needle_count > 0, (
        "the oracle derived no needles, so the privacy test below proves nothing"
    )

    sample = f"repo: {Path.home().as_posix()}/some-clone"
    caught = sum(1 for needle in needles if needle.lower() in sample.lower())
    assert caught, "the oracle failed to flag a literal home path"

    clean = sum(1 for needle in needles if needle.lower() in "FactoryGame/Saved/SaveGames")
    assert not clean, "the oracle flags an ordinary game-relative path, so it is too broad"


def test_the_guard_output_carries_no_personal_data(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = synthetic_docs()
    install = fake_install(tmp_path / "install", raw)
    monkeypatch.setenv(ENV_GAME_DIR, str(install))
    write_pin(pin_path(repo), build_pin(raw, SYNTHETIC_BUILD))

    guard, skips = drift_guard.guard_version_pin(repo)
    rendered = "\n".join([*guard["detail"], *(f"{s['path']} {s['reason']}" for s in skips)])

    # COUNTS and booleans are recorded BEFORE the assertion, and the offending
    # strings are never bound to a local: pytest reprs every local it can
    # reach in the "assert" line of a failure, so binding the list would print
    # the personal data on the very run that proves it must not be printed.
    needles = personal_data_needles()
    lowered = rendered.lower()
    leaked = sum(1 for needle in needles if needle.lower() in lowered)
    account_shaped = _ACCOUNT_ID_SHAPE.search(rendered) is not None
    assert not leaked, (
        f"guard output holds {leaked} of {len(needles)} personal-data strings (content withheld)"
    )
    assert not account_shaped, "guard output holds an account-id-shaped digit run"


def test_the_rendered_repo_line_is_redacted_like_its_sibling_in_verify_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The one line this tool prints on EVERY run must not name a home path.

    Latent only because the settled repository root is not under a home
    directory. A clone that is - a CI checkout, a second working copy - puts
    the operator's account name into the header of every drift-guard run, and
    that header is exactly what gets pasted into an issue.
    """
    operator = tmp_path / "home" / "synthetic-operator"
    clone = operator / "clockspeed-clone"
    clone.mkdir(parents=True)
    monkeypatch.setenv("USERPROFILE", str(operator))

    rendered = "\n".join(drift_guard.render([], [], "test enumeration", clone))

    leaked = "synthetic-operator" in rendered
    assert not leaked, "the repo line named the account directory of a clone under a home path"
    assert "clockspeed-clone" in rendered, (
        "the repo line disappeared rather than being redacted; the header still has to "
        "say which tree was audited"
    )


# ---------------------------------------------------------------------------
# Privacy - the sibling sweep over str(exc)
# ---------------------------------------------------------------------------
#
# str() on a Windows OSError appends the filename it failed on; strerror does
# not. Guard (h) was fixed for that and its seven siblings in the same file
# were not, which is the CONVENTIONS.md section 7 step 5 failure - fix the
# instance, miss the class. One test per site, each driven through the PUBLIC
# entry point that reaches it, so what is proved is that the guard's own error
# path is clean rather than that a helper exists.


def test_the_directory_walk_records_an_unreadable_directory_without_naming_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "iterdir", unreadable)

    _files, _source, skips = drift_guard.enumerate_files(tmp_path)

    assert_reported_without_the_filename(" ".join(skip["reason"] for skip in skips))


def test_the_charset_guard_records_an_unreadable_file_without_naming_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sample = tmp_path / "sample.md"
    sample.write_text("clean\n", encoding="utf-8")
    monkeypatch.setattr(Path, "read_bytes", unreadable)

    _guard, skips = drift_guard.guard_charset(tmp_path, [sample], "test enumeration")

    assert_reported_without_the_filename(" ".join(skip["reason"] for skip in skips))


def test_the_memory_guard_records_an_unreadable_index_without_naming_it(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "read_text", unreadable)

    _guard, skips = drift_guard.guard_memory(repo)

    assert_reported_without_the_filename(" ".join(skip["reason"] for skip in skips))


def test_the_port_guard_reports_an_unreadable_record_without_naming_it(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "read_text", unreadable)

    guard, _skips = drift_guard.guard_ports(repo)

    assert_reported_without_the_filename(" ".join(guard["detail"]))


def test_the_frozen_guard_reports_an_unreadable_claude_md_without_naming_it(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "read_text", unreadable)

    guard, skips = drift_guard.guard_frozen(repo)

    assert_reported_without_the_filename(
        " ".join([*guard["detail"], *(skip["reason"] for skip in skips)])
    )


def test_the_dated_guard_records_unreadable_markdown_without_naming_it(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    markdown = repo / "CLAUDE.md"
    monkeypatch.setattr(Path, "read_text", unreadable)

    _guard, skips = drift_guard.guard_dated(repo, [markdown])

    assert_reported_without_the_filename(" ".join(skip["reason"] for skip in skips))


def test_the_version_pin_guard_reports_an_unreadable_pin_without_naming_it(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The site that was already correct, locked so it cannot regress.

    Guard (h) reached for ``strerror`` before this sweep started. It is
    covered anyway: the seven siblings were wrong precisely because nothing
    held the one correct site in place as a pattern to copy.
    """
    monkeypatch.setattr(Path, "read_text", unreadable)

    guard, skips = drift_guard.guard_version_pin(repo)

    assert_reported_without_the_filename(
        " ".join([*guard["detail"], *(skip["reason"] for skip in skips)])
    )


# ---------------------------------------------------------------------------
# Guard (i) - work-item ownership
# ---------------------------------------------------------------------------

WORK_ITEM_GUARD_ID = "i"

#: State mapped to the owner path the FIXTURE doctrine declares.
#:
#: NONE OF THESE IS A PATH THIS REPOSITORY USES, and that is the point rather
#: than an aesthetic choice. A fixture that restates the real doctrine's four
#: paths verbatim is packed with exactly the belief the guard is unpacked with,
#: so a map HARDCODED to those paths reads the fixture as well as a parse of the
#: doctrine does, and every test built on it passes on both. The fixture would
#: then be grading the guard against its own assumptions. Naming the owner files
#: something the tree has never heard of is what makes the parse load-bearing,
#: and :func:`test_the_fixture_owner_paths_are_not_the_paths_this_repository_uses`
#: keeps it that way as the real doctrine changes.
WORK_ITEM_OWNERS = {
    "OPEN": "PLAN.md",
    "ASPIRATIONAL": "WISHES.md",
    "GATED": "HOLDS.md",
    "CLOSED": "notes/DONE.md",
}

_WORK_ITEM_CLAUDE_MD = """# Fake repository for the drift guard tests

## 5. Session shape

Work-item states, one per item, one file each: OPEN in `PLAN.md`, ASPIRATIONAL in
`WISHES.md`, GATED in `HOLDS.md`, CLOSED in `notes/DONE.md` plus a Settled line
here if it must never reopen.

## 6. Frozen files

- `LICENSE`
"""

_WORK_ITEM_OPEN = """# Fake open-work file

CS-901 - a synthetic open item - acceptance: none - tier: 1
CS-902 - a synthetic open item whose only ledger record is a grant - acceptance: none - tier: 1 -
NOTE: this line mentions CS-903 in its prose, which is a MENTION and not ownership.
"""

_WORK_ITEM_ASPIRATIONAL = """# Fake aspirational file

- A synthetic aspirational line, carrying no ID at all.
"""

_WORK_ITEM_GATED = """# Fake gated file

### CS-G91 - a synthetic gated item

Condition: a synthetic external condition. CS-901 is mentioned here and not owned.
"""

# WHY THIS SYNTHETIC LEDGER DECLARES A SECTION STATUS (CS-840). Guard (g)
# FAILS on a file that carries dated headings and declares nothing, because
# without the declaration it cannot tell a closure record from a live section
# marked historical by its own heading. Every record below opens with a date,
# so this file needs the declaration to reach guard (i) at all.
#
# IT IS DECLARED FOR THE REASON IT IS TRUE, not to quiet a guard: this is the
# synthetic CLOSED owner file, and a file of completion records IS historical.
# Nothing else about the fixture moves - the path stays synthetic, no work
# item ID is added, and the declaration is a bold paragraph rather than a
# heading, so the guard (i) parse this file exists to exercise reads exactly
# what it read before.
_WORK_ITEM_CLOSED = """# Fake closure file

**Section status: HISTORICAL.** Every section in this file is a record.

## Entries

<!-- Newest first. Append new entries immediately below this line. -->
### 2026-08-16 - CS-902 - FROZEN-FILE GRANT ISSUED by the OPERATOR for `LICENSE`
Verification: this entry is the grant record CLAUDE.md section 6 requires BEFORE the
edit, not a completion record. The item it serves is filed in `PLAN.md` as CS-902;
this entry does not close CS-902.

### 2026-08-16 - CS-903 - a synthetic item that genuinely closed
Verification: a synthetic pointer.
"""

_LEDGER_INSERT_ANCHOR = "<!-- Newest first. Append new entries immediately below this line. -->"


def make_work_item_repo(root: Path) -> Path:
    """Build a tree carrying all four work-item owner files, and no collision.

    CS-901 is open only. CS-902 is open AND carries a ledger record, which is
    the grant-before-closure sequence - the shape that has to stay green.
    CS-903 is closed only. CS-G91 is gated only.

    Since CS-1113 :func:`make_repo` builds exactly this tree, because every
    guard has to PASS on the base fixture; the name is kept for the arms below.

    Args:
        root: Directory to build in.

    Returns:
        ``root``, for chaining.
    """
    return make_repo(root)


@pytest.fixture
def work_items(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A fake repository whose four owner files hold no collision.

    Args:
        tmp_path: pytest temporary directory.
        monkeypatch: pytest monkeypatch fixture.

    Returns:
        The fake repository root.
    """
    root = make_work_item_repo(tmp_path / "repo")
    monkeypatch.setattr(drift_guard, "repo_root", lambda: root)
    no_install(monkeypatch, tmp_path)
    return root


def plant_ledger_heading(root: Path, heading: str) -> str:
    """Insert a heading as the NEWEST ledger entry, byte-verifying it applied.

    Args:
        root: The fake repository root.
        heading: The full ``### ...`` line to plant.

    Returns:
        The ledger text as it was BEFORE the plant, so a caller can restore it
        and re-measure.

    Raises:
        AssertionError: The insert anchor was absent or the text did not move.
            A mutation that fails to apply looks exactly like a guard that
            failed to fire (CONVENTIONS.md section 7.2), so this refuses to
            hand back a plant it did not make.
    """
    path = root / WORK_ITEM_OWNERS["CLOSED"]
    before = path.read_text(encoding="utf-8")
    assert _LEDGER_INSERT_ANCHOR in before, (
        "the ledger insert anchor is absent, so this plant would land nowhere"
    )
    after = before.replace(
        _LEDGER_INSERT_ANCHOR,
        f"{_LEDGER_INSERT_ANCHOR}\n{heading}\nVerification: a synthetic pointer.\n",
        1,
    )
    assert after != before, "the plant did not apply"
    path.write_text(after, encoding="utf-8", newline="\n")
    return before


def restore_ledger(root: Path, text: str) -> None:
    """Put a ledger back the way :func:`plant_ledger_heading` found it.

    Args:
        root: The fake repository root.
        text: The text returned by the plant.
    """
    (root / WORK_ITEM_OWNERS["CLOSED"]).write_text(text, encoding="utf-8", newline="\n")


def test_a_planted_duplicate_is_reported_as_drift(
    work_items: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The control. It has to prove the guard FIRES, not that it RUNS.

    A sweep that finds nothing is indistinguishable from a sweep that looks for
    nothing, so the transcript is planted-red then restored-green: the red has
    to be caused BY the plant and has to go away when the plant does.

    DETECTED IS SEPARATED FROM CRASHED. A guard that threw, or that bailed
    before reading an owner file, also reports FAIL - so the assertions below
    require the report to NAME the planted id and BOTH files it collides
    across, and to still show a scanned population. A red carrying none of
    those is a crash wearing a verdict.
    """
    before_code, before_report = run_main(capsys)
    assert (guard_of(before_report, WORK_ITEM_GUARD_ID)["status"], before_code) == ("PASS", 0), (
        "the tree was already red before anything was planted, so a red afterwards "
        "would prove nothing about the plant"
    )

    original = plant_ledger_heading(
        work_items, "### 2026-08-16 - CS-901 - a synthetic closure, planted"
    )
    code, report = run_main(capsys)
    guard = guard_of(report, WORK_ITEM_GUARD_ID)
    rendered = "\n".join(guard["detail"])

    assert guard["status"] == "FAIL"
    assert code != 0, "a collision has to be a non-zero exit code, not only a red word"
    assert report["verdict"] == "DRIFT"
    assert WORK_ITEM_GUARD_ID in report["drift"]
    assert "CS-901" in rendered, (
        f"the guard went red without naming the planted id. It said: {rendered}"
    )
    assert WORK_ITEM_OWNERS["OPEN"] in rendered, (
        f"the guard did not name the file the id is OPEN in: {rendered}"
    )
    assert WORK_ITEM_OWNERS["CLOSED"] in rendered, (
        f"the guard did not name the file the id is CLOSED in: {rendered}"
    )
    assert any("distinct ids found" in line for line in guard["detail"]), (
        "the guard reported no scanned population, so this red is a crash rather than a detection"
    )

    restore_ledger(work_items, original)
    code, report = run_main(capsys)
    assert guard_of(report, WORK_ITEM_GUARD_ID)["status"] == "PASS"
    assert code == 0


def test_a_planted_duplicate_between_two_non_ledger_owner_files_is_reported(
    work_items: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The second acceptance clause, on a pair that is not open-and-closed.

    An item can sit in the open file and the gated file at once, so the second
    clause is graded on that pair rather than on the open-and-closed pair the
    first clause already covers.
    """
    gated = work_items / WORK_ITEM_OWNERS["GATED"]
    before = gated.read_text(encoding="utf-8")
    after = before + "\n### CS-901 - the same synthetic item, now also gated\n"
    assert after != before, "the plant did not apply"
    gated.write_text(after, encoding="utf-8", newline="\n")

    code, report = run_main(capsys)
    guard = guard_of(report, WORK_ITEM_GUARD_ID)
    rendered = "\n".join(guard["detail"])

    assert guard["status"] == "FAIL"
    assert code != 0
    assert "CS-901" in rendered
    assert WORK_ITEM_OWNERS["GATED"] in rendered, (
        f"the guard did not name the gated half of the pair: {rendered}"
    )
    assert WORK_ITEM_OWNERS["OPEN"] in rendered, (
        f"the guard did not name the open half of the pair: {rendered}"
    )


def test_a_ledger_record_that_says_the_item_did_not_close_leaves_it_open(
    work_items: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The sequencing trap, on a synthetic tree, in both directions.

    CS-902 is open AND carries a ledger record, and the record says in its own
    words that it does not close the item. Stripping that sentence out of the
    words that it does not close the item. Stripping that sentence out of the
    record, and leaving the rest of the tree alone, turns the guard red - which
    is what pins the declaration as the thing being read.
    """
    code, report = run_main(capsys)
    assert (guard_of(report, WORK_ITEM_GUARD_ID)["status"], code) == ("PASS", 0)

    path = work_items / WORK_ITEM_OWNERS["CLOSED"]
    before = path.read_text(encoding="utf-8")
    after = before.replace("not a completion record", "a completion record").replace(
        "this entry does not close CS-902", "this entry closes CS-902"
    )
    assert after != before, "the mutation did not apply"
    path.write_text(after, encoding="utf-8", newline="\n")

    code, report = run_main(capsys)
    guard = guard_of(report, WORK_ITEM_GUARD_ID)
    assert guard["status"] == "FAIL", (
        "with its non-closure declaration removed the record is an ordinary closure, "
        "and an ordinary closure beside a live roadmap entry is the CS-204 shape"
    )
    assert "CS-902" in "\n".join(guard["detail"])
    assert code != 0


def test_a_closure_that_a_later_record_reopens_is_not_owned_by_the_ledger(
    work_items: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Newest-first is read as the ledger states it, not as any-mention.

    An item that closed and was then reopened by a correction is OPEN. Planting
    the closure alone is red; planting a newer correction above it is green
    again, with no per-item knowledge anywhere in the guard.
    """
    plant_ledger_heading(work_items, "### 2026-08-16 - CS-901 - a synthetic closure, planted")
    code, report = run_main(capsys)
    assert (guard_of(report, WORK_ITEM_GUARD_ID)["status"], code) == ("FAIL", 1)

    plant_ledger_heading(
        work_items,
        "### 2026-08-17 - CS-901 - CORRECTION: the closure below is wrong, item is reopened",
    )
    code, report = run_main(capsys)
    assert guard_of(report, WORK_ITEM_GUARD_ID)["status"] == "PASS", (
        "the newest record reopens the item, so the older closure below it no longer "
        "makes the ledger an owner"
    )
    assert code == 0


def test_a_tree_with_no_owner_file_declaration_warns_rather_than_passing(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An empty scan says so instead of reporting a green.

    Staged by writing a CLAUDE.md with no work-item sentence in it: since
    CS-1113 the base fixture carries the sentence, because a guard left unread
    there would make every exit code in this module UNGRADED before any plant.

    NOT DRIFT, AND NOT CLEAN EITHER (CS-1113). Nothing was scanned, so the run
    cannot say the tree is clean - the exit code is non-zero and the verdict
    names the class, while the drift list stays empty.
    """
    (repo / "CLAUDE.md").write_text(_CLAUDE_MD, encoding="utf-8")
    code, report = run_main(capsys)
    guard = guard_of(report, WORK_ITEM_GUARD_ID)

    assert guard["status"] == "WARN"
    assert report["verdict"] == "UNGRADED", "a tree with nothing to scan is not DRIFT"
    assert report["drift"] == []
    assert code != 0, "a tree with nothing to scan is not CLEAN either"
    assert any(drift_guard.WORK_ITEM_ANCHOR in skip["reason"] for skip in report["skipped"]), (
        "a guard that scanned nothing has to appear in the skip list saying why"
    )
    assert (repo / "CLAUDE.md").is_file()


def test_declared_owner_files_that_are_all_absent_warn_rather_than_passing(
    work_items: Path,
) -> None:
    """A declaration that names four files none of which are there is not green.

    This is the branch a scope restriction hides in. The doctrine sentence still
    parses, so the guard believes it has a scan population; the files behind it
    are gone, so it has none. Passing here would report CLEAN over a tree where
    every collision is undetectable.
    """
    for relative in WORK_ITEM_OWNERS.values():
        (work_items / relative).unlink()

    guard, skips = drift_guard.guard_work_items(work_items)

    assert guard["status"] == "WARN", (
        f"the guard reported {guard['status']} with no owner file readable: {guard['detail']}"
    )
    assert any("proved nothing on this run" in line for line in guard["detail"])
    assert len(skips) >= drift_guard._COLLISION_FLOOR, (  # noqa: SLF001
        f"a file the doctrine names and the tree lacks has to reach the skip list: {skips}"
    )


def test_owner_files_holding_no_id_at_all_warn_rather_than_passing(work_items: Path) -> None:
    """Present, readable, and empty of items is still a scan that proved nothing."""
    for relative in WORK_ITEM_OWNERS.values():
        (work_items / relative).write_text("# nothing here\n", encoding="utf-8", newline="\n")

    guard, _skips = drift_guard.guard_work_items(work_items)

    assert guard["status"] == "WARN", (
        f"four readable owner files carrying zero ids reported {guard['status']}: {guard['detail']}"
    )
    assert any("proved nothing on this run" in line for line in guard["detail"])


def test_deleting_the_doctrine_sentence_stops_the_scan_loudly(work_items: Path) -> None:
    """The owner-file set is derived, so deleting its source is loud.

    A hand-written tuple of owner files would keep scanning here, which is the
    scope-restriction failure: the list outlives the doctrine it copied.
    """
    guard, _skips = drift_guard.guard_work_items(work_items)
    assert guard["status"] == "PASS"

    path = work_items / "CLAUDE.md"
    before = path.read_text(encoding="utf-8")
    after = "\n".join(
        line for line in before.splitlines() if drift_guard.WORK_ITEM_ANCHOR not in line
    )
    assert after != before, "the deletion did not apply"
    path.write_text(after, encoding="utf-8", newline="\n")

    guard, skips = drift_guard.guard_work_items(work_items)
    assert guard["status"] == "WARN"
    assert any(drift_guard.WORK_ITEM_ANCHOR in skip["reason"] for skip in skips)


# ---------------------------------------------------------------------------
# Guard (i) against the REAL tree - the natural controls
# ---------------------------------------------------------------------------
#
# The oracles below are derived here with their own patterns rather than by
# importing the guard's. Two derivations from one regex agree by construction
# and prove nothing about the tree.

_REAL_ROADMAP_ENTRY = re.compile(r"^(CS-G?\d{2,})\s+-\s", re.MULTILINE)
_REAL_LEDGER_HEADING = re.compile(r"^###\s+\d{4}-\d{2}-\d{2}\s+-\s+([^\n]*?)\s+-\s", re.MULTILINE)
_REAL_ID = re.compile(r"CS-G?\d{2,}")


def real_roadmap_entries(repo_root: Path) -> set[str]:
    """IDs the real ROADMAP.md carries as ENTRY heads.

    Args:
        repo_root: The repository root.

    Returns:
        The owned IDs.
    """
    text = (repo_root / "ROADMAP.md").read_text(encoding="utf-8")
    return set(_REAL_ROADMAP_ENTRY.findall(text))


def real_ledger_heading_ids(repo_root: Path) -> set[str]:
    """IDs named at the head of a real docs/LEDGER.md record, closure or not.

    Args:
        repo_root: The repository root.

    Returns:
        Every ID appearing in a record heading.
    """
    text = (repo_root / "docs" / "LEDGER.md").read_text(encoding="utf-8")
    return {item for head in _REAL_LEDGER_HEADING.findall(text) for item in _REAL_ID.findall(head)}


def test_the_real_tree_carries_ids_in_both_the_roadmap_and_the_ledger(repo_root: Path) -> None:
    """The floor. Without this the green below is a claim about an empty set.

    This is the sequencing trap standing in the tree rather than staged in a
    fixture: a frozen-file grant is recorded BEFORE the edit it authorises, so
    an item is legitimately named in the ledger while still open. CS-436's
    2026-08-16 grant is the instance that earned this test; the assertion
    quantifies over whatever the tree holds so that it survives that item
    closing.
    """
    overlap = real_roadmap_entries(repo_root) & real_ledger_heading_ids(repo_root)
    assert overlap, (
        "no open roadmap item is named anywhere in the ledger, so the two tests "
        "below are green about nothing. If the tree genuinely has no such item, "
        "this fixture-free control has to be replaced by a staged one rather than "
        "deleted."
    )


def test_the_real_tree_is_green_on_every_open_item_the_ledger_already_names(
    repo_root: Path,
) -> None:
    """Green on correct history, and it says WHY for each id it forgives.

    A guard red here would be red against a grant record that CLAUDE.md section
    6 REQUIRES to exist before the edit. That is the shape that gets switched
    off rather than obeyed, so it is graded on the real file rather than on a
    fixture.
    """
    overlap = real_roadmap_entries(repo_root) & real_ledger_heading_ids(repo_root)
    guard, _skips = drift_guard.guard_work_items(repo_root)
    rendered = "\n".join(guard["detail"])

    assert guard["status"] == "PASS", (
        f"the work-item guard is red on the tree as it stands. Ids named in both "
        f"the roadmap and the ledger right now: {sorted(overlap)}. Detail:\n{rendered}"
    )
    unexplained = [item for item in sorted(overlap) if item not in rendered]
    assert not unexplained, (
        f"{unexplained} are open AND named in the ledger, and the guard reported no "
        "reason for treating them as open. A forgiveness with no stated basis is an "
        "allowlist."
    )


def test_an_id_merely_mentioned_in_a_roadmap_note_is_not_owned_there(repo_root: Path) -> None:
    """Mention is not ownership, measured on the real roadmap.

    A roadmap NOTE cites the closed items that earned the entry - CS-211's own
    NOTE is written around one - so a guard matching an ID anywhere in the file
    would report those citations as collisions.
    """
    text = (repo_root / "ROADMAP.md").read_text(encoding="utf-8")
    mentioned = set(_REAL_ID.findall(text)) - real_roadmap_entries(repo_root)
    guard, _skips = drift_guard.guard_work_items(repo_root)
    closed_elsewhere = mentioned & real_ledger_heading_ids(repo_root)

    assert closed_elsewhere, (
        "the roadmap mentions no id that the ledger also names, so this control "
        "has nothing to discriminate and its green means nothing"
    )
    assert guard["status"] == "PASS", (
        f"ids mentioned but not owned by the roadmap: {sorted(closed_elsewhere)}. "
        "Each is cited in the prose of an entry it is not the subject of."
    )


def test_the_real_scan_population_is_non_empty_across_the_owner_files(repo_root: Path) -> None:
    """A floor under the scan itself, so a silent zero cannot pass as green."""
    guard, _skips = drift_guard.guard_work_items(repo_root)
    census = [line for line in guard["detail"] if " owns " in line]
    owning = [line for line in census if not line.endswith("owns 0 id(s)")]

    assert len(census) >= drift_guard._COLLISION_FLOOR, (  # noqa: SLF001
        f"only {len(census)} owner file(s) were read. A collision needs two, so "
        f"below that the cross-file check is vacuous by construction: {census}"
    )
    assert len(owning) >= drift_guard._COLLISION_FLOOR, (  # noqa: SLF001
        f"only {len(owning)} owner file(s) actually own an id: {census}"
    )
    assert any("distinct ids found" in line for line in guard["detail"])


# ---------------------------------------------------------------------------
# Guard (i) - the forgiveness predicate is SCOPED to the record's own item
# ---------------------------------------------------------------------------
#
# A non-closure declaration is an EXEMPTION, and an exemption that can be
# triggered by prose written for some other purpose is an allowlist nobody
# audited. The three tests below are the three ways a document-wide phrase
# search grants one: a sentence about a DIFFERENT item, a GENERIC sentence
# about no item, and a sentence belonging to a LATER heading absorbed into the
# record above. Each plants an ordinary CS-204-shaped closure - open in one
# owner file, closed in another - so a guard that forgives it is green on the
# exact defect the item was filed for.


def plant_ledger_record(root: Path, record: str) -> None:
    """Insert a whole record, heading and body, as the NEWEST ledger entry.

    :func:`plant_ledger_heading` supplies its own one-line body, which is the
    wrong instrument when the BODY is the thing under test.

    Args:
        root: The fake repository root.
        record: The record text, starting with its ``###`` heading line.

    Raises:
        AssertionError: The insert anchor was absent or the text did not move.
            A plant that fails to apply looks exactly like a guard that failed
            to fire, so this refuses to leave one unnoticed.
    """
    path = root / WORK_ITEM_OWNERS["CLOSED"]
    before = path.read_text(encoding="utf-8")
    assert _LEDGER_INSERT_ANCHOR in before, (
        "the ledger insert anchor is absent, so this plant would land nowhere"
    )
    after = before.replace(_LEDGER_INSERT_ANCHOR, f"{_LEDGER_INSERT_ANCHOR}\n{record}\n", 1)
    assert after != before, "the plant did not apply"
    path.write_text(after, encoding="utf-8", newline="\n")


def work_item_guard(root: Path) -> tuple[str, str]:
    """Run guard (i) against a root and return its status and rendered detail.

    Args:
        root: The repository root to scan.

    Returns:
        ``(status, rendered detail)``.
    """
    guard, _skips = drift_guard.guard_work_items(root)
    return guard["status"], "\n".join(guard["detail"])


def test_a_non_closure_sentence_about_a_different_item_does_not_forgive_a_closure(
    work_items: Path,
) -> None:
    """A true sentence about ANOTHER item must not exempt this record.

    This is the CS-204 shape with one ordinary sentence added. CS-901 is open
    in the roadmap and this record closes it; the record also remarks, truly,
    that a different item is untouched. Reading the remark as this record's
    disposition forgives a real collision, and does it silently.
    """
    assert work_item_guard(work_items)[0] == "PASS", "the tree was red before the plant"

    plant_ledger_record(
        work_items,
        "### 2026-08-16 - CS-901 - a synthetic closure, planted\n"
        "Verification: a synthetic pointer. CS-903 stays open and is untouched by this item.",
    )

    status, rendered = work_item_guard(work_items)
    assert status == "FAIL", (
        "a sentence about CS-903 was read as CS-901's disposition, so the closure "
        f"was forgiven and the collision went unreported. The guard said:\n{rendered}"
    )
    assert "CS-901" in rendered


def test_a_generic_sentence_naming_no_item_does_not_forgive_a_closure(work_items: Path) -> None:
    """A statement about records IN GENERAL is not a statement about this item.

    The sentence planted here is the most natural one-line summary of what a
    ledger record for the work-item guard itself would say. It describes the
    class of grant records, names no item, and decides nothing - so reading it
    as this record's disposition means the guard cannot close its own item.
    """
    assert work_item_guard(work_items)[0] == "PASS", "the tree was red before the plant"

    plant_ledger_record(
        work_items,
        "### 2026-08-16 - CS-901 - a synthetic closure, planted\n"
        "Verification: a grant record does not close the item it names, and the guard knows it.",
    )

    status, rendered = work_item_guard(work_items)
    assert status == "FAIL", (
        "a generic sentence about grant records was read as CS-901's own disposition. "
        f"The guard said:\n{rendered}"
    )
    assert "CS-901" in rendered


def test_a_later_heading_without_an_item_id_cannot_forgive_the_record_above_it(
    work_items: Path,
) -> None:
    """A heading that owns no item still ENDS the record above it.

    A ``###`` heading carrying no work-item ID is not a record head. If it is
    also not a record BOUNDARY its body merges upward, and any later note that
    happens to say "stays open" exempts a clean closure written before it.
    """
    assert work_item_guard(work_items)[0] == "PASS", "the tree was red before the plant"

    plant_ledger_record(
        work_items,
        "### 2026-08-16 - CS-901 - a synthetic closure, planted\n"
        "Verification: a synthetic pointer.\n"
        "\n"
        "### Follow-up note carrying no work-item id\n"
        "The sibling sweep stays open and is tracked separately.",
    )

    status, rendered = work_item_guard(work_items)
    assert status == "FAIL", (
        "the body of a later id-less heading was absorbed into the record above and "
        f"exempted it. The guard said:\n{rendered}"
    )
    assert "CS-901" in rendered


def test_a_record_that_binds_its_declaration_to_its_own_id_is_still_forgiven(
    work_items: Path,
) -> None:
    """The other direction, so the scoping above is not merely a blanket refusal.

    Narrowing an exemption is only correct if the exemption still works. This
    plants the same closure heading with a declaration that NAMES the item it
    is about, which is the shape every grant record in the tree already uses,
    and requires it to stay green.
    """
    plant_ledger_record(
        work_items,
        "### 2026-08-16 - CS-901 - a synthetic record, planted\n"
        "Verification: a synthetic pointer. This entry does not close CS-901.",
    )

    status, rendered = work_item_guard(work_items)
    assert status == "PASS", (
        f"a declaration naming its own item was refused, which is a red against a "
        f"correctly written record. The guard said:\n{rendered}"
    )
    assert "CS-901" in rendered, "a forgiveness has to be reported, not merely granted"


# ---------------------------------------------------------------------------
# Guard (i) - an owner clause that stops parsing is UNACCOUNTED, never dropped
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", sorted(WORK_ITEM_OWNERS))
def test_rewording_an_owner_clause_is_reported_rather_than_silently_dropped(
    work_items: Path, state: str
) -> None:
    """Every clause, one at a time. A parse that reads FEWER files must be loud.

    A scope restriction is an allowlist with the sign flipped: whatever leaves
    the scan takes its coverage with it and nothing goes red. Rewording one
    clause of the doctrine sentence - same files, same meaning - is the
    cheapest way to make a file leave the scan, so it is graded on all four
    rather than on the one that happened to be tried.

    Args:
        work_items: The fake repository root.
        state: The work-item state whose clause is reworded.
    """
    relative = WORK_ITEM_OWNERS[state]
    path = work_items / "CLAUDE.md"
    before = path.read_text(encoding="utf-8")
    after = before.replace(f"{state} in", f"{state} work lives in", 1)
    assert after != before, f"the reword did not apply for {state}"
    path.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = work_item_guard(work_items)
    assert status == "FAIL", (
        f"the {state} clause stopped parsing and {relative} left the scan with nothing "
        f"red. The guard said:\n{rendered}"
    )
    assert relative in rendered, (
        f"the guard went red without naming the file that left the scan: {rendered}"
    )


def test_renaming_an_owner_file_in_the_doctrine_moves_the_scan_with_it(work_items: Path) -> None:
    """The owner map is READ, not believed.

    A hardcoded map keeps scanning the old path here and reports a clean tree
    over a file it never opened. Renaming on disk AND in the doctrine has to
    move the scan, and renaming on disk ALONE has to be loud.
    """
    relative = WORK_ITEM_OWNERS["GATED"]
    moved = "notes/PARKED.md"
    (work_items / moved).parent.mkdir(parents=True, exist_ok=True)
    (work_items / relative).rename(work_items / moved)

    status, rendered = work_item_guard(work_items)
    assert status != "PASS", (
        f"the doctrine still names {relative} and the file is gone, and the guard was "
        f"green anyway:\n{rendered}"
    )

    path = work_items / "CLAUDE.md"
    before = path.read_text(encoding="utf-8")
    after = before.replace(f"`{relative}`", f"`{moved}`", 1)
    assert after != before, "the doctrine rename did not apply"
    path.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = work_item_guard(work_items)
    assert status == "PASS", f"the scan did not follow the doctrine to {moved}:\n{rendered}"
    assert moved in rendered, f"the census does not name the renamed file: {rendered}"


def test_the_fixture_owner_paths_are_not_the_paths_this_repository_uses(
    repo_root: Path,
) -> None:
    """The fixture must not agree with the implementation by construction.

    A fixture that restates the real doctrine's four paths verbatim is packed
    with the belief the guard is unpacked with, so a hardcoded map satisfies it
    exactly as well as a parse does and no test can tell them apart. These
    paths are deliberately not the ones this repository owns.

    Args:
        repo_root: The repository root.
    """
    doctrine = (repo_root / "CLAUDE.md").read_text(encoding="utf-8")
    real = set(re.findall(r"\b[A-Z]{3,}\s+in\s+`([^`]+)`", doctrine))
    assert real, "the real doctrine sentence parsed to nothing, so this control is vacuous"
    fixture = set(WORK_ITEM_OWNERS.values())
    assert not (real & fixture), (
        f"the fixture reuses the real owner paths {sorted(real & fixture)}, so a map "
        "hardcoded to those paths would read the fixture and every test here would "
        "pass on it"
    )


# ---------------------------------------------------------------------------
# Guard (i) - an unread entry head is UNACCOUNTED, and the floor counts owners
# ---------------------------------------------------------------------------


def test_a_head_shape_the_recogniser_cannot_read_is_reported_rather_than_skipped(
    work_items: Path,
) -> None:
    """An unrecognised head must be UNACCOUNTED, not UNREAD.

    The two failure directions are not symmetric. A head the recogniser misses
    removes an item from the scan and the report stays green, so the tree looks
    clean because less of it was read. Naming the line is the whole remedy: the
    author either rewrites the head or the recogniser learns the shape.
    """
    path = work_items / WORK_ITEM_OWNERS["OPEN"]
    before = path.read_text(encoding="utf-8")
    after = f"{before}CS-904 (open) - a head shape the recogniser does not know\n"
    assert after != before, "the plant did not apply"
    path.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = work_item_guard(work_items)
    assert status == "FAIL", (
        f"a line carrying an id in a head position was silently unread:\n{rendered}"
    )
    assert "CS-904" in rendered, f"the guard went red without naming the line: {rendered}"


def test_an_id_named_in_ordinary_prose_is_not_reported_as_an_unread_head(
    work_items: Path,
) -> None:
    """The other direction, measured on the real tree's own prose shapes.

    A ledger body wraps, so a line can BEGIN with an id and still be the middle
    of a sentence. Reporting those as unread heads would be a red against
    correct history, which gets the guard switched off rather than obeyed.
    """
    path = work_items / WORK_ITEM_OWNERS["CLOSED"]
    before = path.read_text(encoding="utf-8")
    after = (
        f"{before}\n### 2026-08-16 - CS-905 - a synthetic closure\n"
        "Verification: a synthetic pointer.\n"
        "CS-903 is not revisited; its measurement stays as recorded.\n"
        "CS-903's grading half was checked separately.\n"
        "**CS-903 IS NOT REOPENED BY THIS.**\n"
    )
    assert after != before, "the plant did not apply"
    path.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = work_item_guard(work_items)
    assert status == "PASS", (
        f"a wrapped prose line beginning with an id was reported as an unread head:\n{rendered}"
    )


def test_the_floor_counts_owner_files_that_actually_own_an_id(work_items: Path) -> None:
    """Files READ is not the population a cross-file collision needs.

    Reformatting entries so no line is a head leaves the file present, readable
    and worth nothing to this guard. Counting it toward the floor lets the
    whole OPEN half leave the scan while the report still shows four owner
    files and a clean verdict.
    """
    for state in ("OPEN", "GATED"):
        path = work_items / WORK_ITEM_OWNERS[state]
        path.write_text(
            f"# Fake {state.lower()} file with no entry head\n\n"
            "The synthetic item CS-901 is discussed here in prose and owned nowhere.\n",
            encoding="utf-8",
            newline="\n",
        )

    status, rendered = work_item_guard(work_items)
    assert status == "WARN", (
        "one owner file owning every id it found is not a population a collision can "
        f"exist in, and the guard reported {status}:\n{rendered}"
    )
    assert "proved nothing on this run" in rendered


# ---------------------------------------------------------------------------
# GUARD (b), THE MEMORY PARTITION - BOTH DIRECTIONS, EACH WITH ITS OWN CONTROL
# ---------------------------------------------------------------------------
# CS-890. The guard asserted ONE direction of a partition - every leaf is named
# by a token the index can reach - and called that reachability. A token naming
# nothing is an element that simply matches nothing, so the other direction was
# never asserted at all: a dangling wikilink inside a leaf was invisible, and
# the INDEX ITSELF could route to a file that does not exist, both while the
# guard reported CLEAN. That is CS-497's shape one store over - a partition
# asserted one way round is a subset check wearing a partition's name.
#
# THREE ARMS, THREE CONTROLS, ONE STATUS. The three findings have three
# distinct remedies, so each gets its own arm; they are two directions of one
# partition, so they stay inside guard (b) and one verdict. Each red arm is
# paired with a green control, because an arm that reddens on everything is
# not evidence that it reddens on the right thing.
#
# WHY THESE RUN ON A COPY OF THE REAL STORE rather than a synthetic one. The
# trap this guard walks into is specific to the real index's content: it
# carries `assert count == 0` and `git commit -F` in BACKTICKS, and the
# reachability extractor harvests backticked spans on purpose. A resolution
# check built on that extractor would demand both name files and would
# manufacture two findings the moment it shipped. No hand-authored fixture
# would have carried those two strings, so no hand-authored fixture could have
# caught it. The synthetic-fixture rule this project holds is about GAME data
# (CLAUDE.md section 7); memory/ is the repository's own tracked prose, and the
# file the operator actually reads is the only one worth a green about.

#: A leaf stem this repository has never had. Every plant below asserts its
#: absence before planting - a plant that accidentally named a real file would
#: prove nothing, and would look exactly like a plant that worked.
GHOST_LEAF = "zz-synthetic-ghost-leaf-cs890"

#: Wikilink and markdown-link shapes, re-derived here rather than imported from
#: the guard. Two derivations from one regex agree by construction, so the
#: population these controls assert is non-empty has to come from somewhere the
#: guard cannot reach.
_TEST_WIKILINK = re.compile(r"\[\[([^\]|#]+)\]\]")
_TEST_MDLINK = re.compile(r"\]\(([^)\s]+)\)")

#: LINK-SHAPED TOKENS THAT SIT INSIDE CODE IN THE TRACKED STORE, and are
#: therefore not citations. Enumerated BY HAND from reading the files, as
#: ``(file, kind, target)``, so the expected counts below owe NOTHING to any
#: code model.
#:
#: THE PREVIOUS VERSION OF THIS ORACLE WAS A LINE-FOR-LINE CLONE of the
#: guard's own scanner - same algorithm, same branch order, same escape hatch
#: for a backtick in an info string. On every pathology it agreed with the
#: guard by construction, so the equality assertion stayed green while the
#: guard manufactured findings. A second typing of one algorithm is not a
#: second opinion.
#:
#: A new in-code token added to the store makes this list stale and the count
#: arm RED. That is intended: it forces a human to look at the new token and
#: decide whether it is code or a real dangling citation.
KNOWN_IN_CODE_TOKENS = {
    ("a-guard-can-be-accepted-and-unscoped.md", "w", "tool.mypy.overrides"),
}


def memory_copy(tmp_path: Path) -> Path:
    """Copy the tracked memory store into a fake repository root.

    Nothing here writes ``memory/`` in the repository. Every plant lands on
    this copy, so a test that crashes mid-plant cannot leave the operator's
    durable store corrupted.

    Args:
        tmp_path: pytest temporary directory.

    Returns:
        The fake repository root, with ``memory/`` populated.
    """
    root = tmp_path / "memory-store"
    root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(REPO_ROOT / "memory", root / "memory")
    return root


def memory_verdict(root: Path) -> tuple[str, str]:
    """Run guard (b) against ``root`` and return its status and rendered detail.

    Args:
        root: The repository root to grade.

    Returns:
        ``(status, rendered detail)``.
    """
    guard, _skips = drift_guard.guard_memory(root)
    return guard["status"], "\n".join(guard["detail"])


def raw_citations(path: Path) -> set[tuple[str, str]]:
    """Every link-shaped token in a file, with NO code model whatsoever.

    Deliberately naive: it does not know what a fence is, what an inline span
    is, or what a blockquote is. That naivety is the point - it is what makes
    it a genuinely different oracle from the guard rather than a second typing
    of the guard's own algorithm. The code-shaped tokens it over-collects are
    subtracted from a HAND-WRITTEN list instead.

    Args:
        path: The markdown file to scan.

    Returns:
        Distinct ``(kind, target)`` pairs, kind being "w" or "m".
    """
    text = path.read_text(encoding="utf-8")
    found = {("w", token.strip()) for token in _TEST_WIKILINK.findall(text)}
    return found | {("m", token.strip()) for token in _TEST_MDLINK.findall(text)}


def expected_citation_counts(memory_dir: Path) -> tuple[int, int]:
    """Citation counts derived without any notion of code.

    Args:
        memory_dir: The ``memory`` directory to scan.

    Returns:
        ``(index citations, leaf citations)``, partitioned the way the guard
        partitions them - MEMORY.md and its INDEX_*.md children on one side.

    Raises:
        AssertionError: The hand-written in-code list names a token that is
            no longer in the store, which would silently inflate the expected
            count.
    """
    index_total = 0
    leaf_total = 0
    for path in sorted(memory_dir.glob("*.md")):
        found = raw_citations(path)
        excluded = {
            (kind, target) for name, kind, target in KNOWN_IN_CODE_TOKENS if name == path.name
        }
        stale = excluded - found
        assert not stale, f"KNOWN_IN_CODE_TOKENS names {stale} which is not in {path.name}"
        count = len(found - excluded)
        if path.name == "MEMORY.md" or path.name.lower().startswith("index_"):
            index_total += count
        else:
            leaf_total += count
    return index_total, leaf_total


def reported_citation_counts(rendered: str) -> tuple[int, int]:
    """Pull the two population sizes out of guard (b)'s own detail lines.

    Args:
        rendered: The guard's joined detail.

    Returns:
        ``(index citations checked, leaf citations checked)``.
    """
    index_line = re.search(r"index citations resolved[^:]*: (\d+) of (\d+)", rendered)
    leaf_line = re.search(r"leaf citations resolved[^:]*: (\d+) of (\d+)", rendered)
    assert index_line is not None, f"no index count line in:\n{rendered}"
    assert leaf_line is not None, f"no leaf count line in:\n{rendered}"
    return int(index_line.group(2)), int(leaf_line.group(2))


def test_the_real_memory_store_passes_the_memory_guard_on_a_non_empty_population(
    tmp_path: Path,
) -> None:
    """The pristine store is CLEAN, and the population that green covers is real.

    An empty population satisfies every zero, so the count assertions come
    first. They are derived with this module's own patterns rather than the
    guard's, because a green about a population the guard alone defined is a
    green about the guard's opinion of itself.
    """
    root = memory_copy(tmp_path)
    store = sorted((root / "memory").glob("*.md"))
    wikilinks = 0
    mdlinks = 0
    for path in store:
        found = raw_citations(path)
        wikilinks += sum(1 for kind, _target in found if kind == "w")
        mdlinks += sum(1 for kind, _target in found if kind == "m")

    assert len(store) > 1, "a store with no leaves proves nothing about reachability"
    assert wikilinks > 0, "no wikilink outside a fence - the leaf-citation arm graded nothing"
    assert mdlinks > 0, "no markdown link outside a fence - the routing arm graded nothing"

    status, rendered = memory_verdict(root)
    assert status == "PASS", (
        f"the tracked memory store is not clean under its own guard:\n{rendered}"
    )


def test_a_dangling_wikilink_inside_a_leaf_reddens_the_memory_guard(tmp_path: Path) -> None:
    """The filed CS-890 fault: a leaf cites a note that does not exist.

    ``reachable_from_index`` never opens an ordinary leaf, so before this
    change the plant below was invisible and the guard reported PASS.
    """
    root = memory_copy(tmp_path)
    leaf = next(path for path in sorted((root / "memory").glob("*.md")) if path.name != "MEMORY.md")
    assert not (root / "memory" / f"{GHOST_LEAF}.md").exists(), "the plant names a real file"

    before = leaf.read_text(encoding="utf-8")
    after = f"{before}\nThe lesson is owned by [[{GHOST_LEAF}]].\n"
    assert after != before, "the plant did not apply"
    leaf.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = memory_verdict(root)
    assert status == "FAIL", (
        f"a leaf cites a note that does not exist and the guard said {status}:\n{rendered}"
    )
    assert GHOST_LEAF in rendered, "the guard failed without naming the dangling target"
    assert leaf.name in rendered, "the guard failed without naming the file the citation is in"


def test_a_markdown_link_in_the_index_naming_a_ghost_leaf_reddens_the_memory_guard(
    tmp_path: Path,
) -> None:
    """The wider fault: the routing table itself points at a file that is absent.

    Worse than an unindexed leaf, because the index is what the next session
    reads to find anything at all.
    """
    root = memory_copy(tmp_path)
    index = root / "memory" / "MEMORY.md"
    assert not (root / "memory" / f"{GHOST_LEAF}.md").exists(), "the plant names a real file"

    before = index.read_text(encoding="utf-8")
    after = f"{before}\n- [A ghost]({GHOST_LEAF}.md) - routes nowhere.\n"
    assert after != before, "the plant did not apply"
    index.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = memory_verdict(root)
    assert status == "FAIL", (
        f"the index routes to a file that does not exist and the guard said {status}:\n{rendered}"
    )
    assert GHOST_LEAF in rendered, "the guard failed without naming the ghost the index routes to"


def test_a_wikilink_in_the_index_naming_a_ghost_leaf_reddens_the_memory_guard(
    tmp_path: Path,
) -> None:
    """The same direction in the other citation shape.

    The index carries markdown links today and no wikilinks, so a routing
    check written against markdown links alone would be green on the day
    someone writes the first index wikilink.
    """
    root = memory_copy(tmp_path)
    index = root / "memory" / "MEMORY.md"
    assert not (root / "memory" / f"{GHOST_LEAF}.md").exists(), "the plant names a real file"

    before = index.read_text(encoding="utf-8")
    after = f"{before}\n- [[{GHOST_LEAF}]] - routes nowhere.\n"
    assert after != before, "the plant did not apply"
    index.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = memory_verdict(root)
    assert status == "FAIL", (
        f"an index wikilink names a file that does not exist and the guard said "
        f"{status}:\n{rendered}"
    )
    assert GHOST_LEAF in rendered, "the guard failed without naming the ghost the index routes to"


def test_an_unindexed_leaf_still_fails_the_memory_guard_naming_it(tmp_path: Path) -> None:
    """POSITIVE CONTROL for the direction that already bit.

    This one FAILED before the second direction was added and has to keep
    failing after. A repair that adds a direction while silently breaking the
    one that worked is a net loss, and is exactly the CS-497 shape repeating.
    The leaf is chosen by derivation rather than by name so a rename cannot
    turn this control green.
    """
    root = memory_copy(tmp_path)
    index = root / "memory" / "MEMORY.md"
    before = index.read_text(encoding="utf-8")
    targets = _TEST_MDLINK.findall(before)
    assert targets, "the index links nothing, so unindexing one entry proves nothing"
    victim = targets[0]
    assert (root / "memory" / victim).is_file(), "the chosen entry does not name a real leaf"

    kept = [line for line in before.splitlines(keepends=True) if victim not in line]
    after = "".join(kept)
    assert after != before, "the plant did not apply"
    index.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = memory_verdict(root)
    assert status == "FAIL", (
        f"a real leaf was removed from the index and the guard said {status}:\n{rendered}"
    )
    assert victim in rendered, "the guard failed without naming the leaf it can no longer reach"


def test_a_wikilink_shaped_token_inside_a_fenced_block_is_not_a_citation(
    tmp_path: Path,
) -> None:
    """A fenced TOML array-of-tables header is sample material, not a link.

    The store quotes ``[[tool.mypy.overrides]]`` inside a fence. It is spelled
    exactly like a wikilink and cites nothing, so resolving it would make the
    guard red on correct content - the one failure mode that would block every
    commit in the repository.
    """
    root = memory_copy(tmp_path)
    leaf = next(path for path in sorted((root / "memory").glob("*.md")) if path.name != "MEMORY.md")
    before = leaf.read_text(encoding="utf-8")
    after = f"{before}\n```\n[[{GHOST_LEAF}.section]]\nkey = 1\n```\n"
    assert after != before, "the plant did not apply"
    leaf.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = memory_verdict(root)
    assert status == "PASS", (
        f"a wikilink-shaped token inside a fence was resolved as a citation:\n{rendered}"
    )


def test_a_dangling_wikilink_directly_above_a_fence_still_reddens(tmp_path: Path) -> None:
    """The fenced exclusion is scoped to fences, not to anything awkward nearby.

    Without this control, an extractor that gave up on the whole file the
    moment it met a fence would pass every other arm in this section.
    """
    root = memory_copy(tmp_path)
    leaf = next(path for path in sorted((root / "memory").glob("*.md")) if path.name != "MEMORY.md")
    assert not (root / "memory" / f"{GHOST_LEAF}.md").exists(), "the plant names a real file"

    before = leaf.read_text(encoding="utf-8")
    after = f"{before}\nSee [[{GHOST_LEAF}]].\n\n```\n[[tool.mypy.overrides]]\n```\n"
    assert after != before, "the plant did not apply"
    leaf.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = memory_verdict(root)
    assert status == "FAIL", (
        f"a dangling wikilink one line above a fence was excluded with it:\n{rendered}"
    )
    assert GHOST_LEAF in rendered, "the guard failed without naming the dangling target"


def test_a_backticked_code_span_in_the_index_is_not_resolved_as_a_citation(
    tmp_path: Path,
) -> None:
    """THE TRAP, graded directly rather than left to the pristine control.

    ``link_targets`` harvests backticked spans, which is correct for
    reachability and wrong for resolution. The index carries at least two
    backticked spans that are code, not filenames; a routing check built on
    that extractor manufactures a finding per span. This arm plants a third,
    so the trap is graded on a token this test owns rather than on two strings
    a future edit to the index might remove.
    """
    root = memory_copy(tmp_path)
    index = root / "memory" / "MEMORY.md"
    existing = _TEST_MDLINK.findall(index.read_text(encoding="utf-8"))
    assert existing, "the index links nothing, so this arm would pass on an empty index"

    before = index.read_text(encoding="utf-8")
    after = f"{before}\nRun `pytest -q tests/` and assert `count == 0` before believing it.\n"
    assert after != before, "the plant did not apply"
    index.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = memory_verdict(root)
    assert status == "PASS", (
        f"a backticked code span in the index was resolved as a file citation:\n{rendered}"
    )


def test_an_external_url_in_a_leaf_is_not_resolved_against_the_store(tmp_path: Path) -> None:
    """A URL is not a claim about this store and is never failed as one.

    The store carries no external link today, so nothing else in this section
    would notice a resolver that treated one as a missing leaf. That green
    would last exactly until the first note cited a specification.
    """
    root = memory_copy(tmp_path)
    leaf = next(path for path in sorted((root / "memory").glob("*.md")) if path.name != "MEMORY.md")
    before = leaf.read_text(encoding="utf-8")
    link = "[the spec](https://example.invalid/spec.md#section)"
    after = f"{before}\nSee {link} for the wire form.\n"
    assert after != before, "the plant did not apply"
    leaf.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = memory_verdict(root)
    assert status == "PASS", f"an external URL was resolved as a path inside memory/:\n{rendered}"


def test_an_unterminated_fence_is_reported_rather_than_swallowed(tmp_path: Path) -> None:
    """An open fence blanks an arbitrary SUFFIX, so it may not read as clean.

    This arm used to assert PASS plus a skip record, on the reasoning that an
    unbalanced fence is a formatting fault rather than a broken citation. That
    was too weak. An open fence removes everything after it from the
    population, so a guard that reported a clean count over it would be
    reporting a green about a region it never read - which is
    ``memory/an-empty-population-satisfies-every-zero.md`` happening inside
    the guard that protects that store.

    Failing is safe here: an unterminated fence is malformed markdown, and no
    file in the tracked store carries one - asserted below rather than
    assumed, so this arm grades a reachable state and not a hypothesis.
    """
    root = memory_copy(tmp_path)
    memory = root / "memory"
    pristine_status, pristine = memory_verdict(root)
    assert pristine_status == "PASS", (
        "the store is not clean before the plant, so this arm cannot attribute the "
        f"failure below to its own fence:\n{pristine}"
    )

    leaf = next(path for path in sorted(memory.glob("*.md")) if path.name != "MEMORY.md")
    before = leaf.read_text(encoding="utf-8")
    after = f"{before}\n```\nnever closed\n\nSee [[{GHOST_LEAF}]].\n"
    assert after != before, "the plant did not apply"
    leaf.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = memory_verdict(root)
    assert status == "FAIL", (
        f"an unterminated fence hid the rest of a file and the guard said {status}:\n{rendered}"
    )
    assert leaf.name in rendered, "the guard failed without naming the file it could not read"
    assert "UNTERMINATED CODE FENCE" in rendered, (
        f"the finding does not say WHY the file went unread:\n{rendered}"
    )


def test_a_child_index_routing_to_a_ghost_fails_under_the_routing_heading(
    tmp_path: Path,
) -> None:
    """LEG 2 follows INDEX_*.md children, and the store cannot exercise that.

    ``memory/`` is flat today - MEMORY.md plus leaves, no domain index - so
    every other arm in this section grades the routing leg on ONE file. The
    transitive walk is live code all the same, and an untested branch in a
    guard the pre-commit and pre-push paths both run is the branch that breaks
    quietly.

    The heading is asserted, not just the status. A ghost in a child index is a
    ROUTING fault whose remedy is "fix the entry"; classifying it with the leaf
    cross-references would hand the reader the wrong instruction, and one
    status for three findings is only safe while each finding says which of
    the three it is.
    """
    root = memory_copy(tmp_path)
    memory = root / "memory"
    child = memory / "INDEX_probe.md"
    assert not child.exists(), "the store already has a child index, so this plant is not additive"
    child.write_text(
        "# Probe index\n\n- [A ghost](zz-probe-ghost-leaf.md) - routes nowhere.\n",
        encoding="utf-8",
        newline="\n",
    )
    assert not (memory / "zz-probe-ghost-leaf.md").exists(), "the plant names a real file"

    index = memory / "MEMORY.md"
    before = index.read_text(encoding="utf-8")
    after = f"{before}\n- [Probe](INDEX_probe.md) - a child index.\n"
    assert after != before, "the plant did not apply"
    index.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = memory_verdict(root)
    assert status == "FAIL", (
        f"a child index routing to a ghost was not caught; the guard said {status}:\n{rendered}"
    )
    assert "zz-probe-ghost-leaf" in rendered, "the guard failed without naming the ghost"
    assert child.name in rendered, "the guard failed without naming the child index"
    routing_heading = "THE INDEX ROUTES TO A FILE THAT DOES NOT EXIST:"
    assert routing_heading in rendered, (
        f"a child index is a routing file, so its ghost belongs under {routing_heading!r}; "
        f"the guard reported:\n{rendered}"
    )
    assert "A LEAF CITES A NOTE THAT DOES NOT EXIST:" not in rendered, (
        "a child index was graded as an ordinary leaf, so the reader is handed the wrong "
        f"remedy:\n{rendered}"
    )


def test_a_child_index_whose_links_all_resolve_keeps_the_guard_green(tmp_path: Path) -> None:
    """The control for the arm above: the walk is not red on everything.

    Without this, an implementation that failed EVERY child index would pass
    the arm above and still be broken.
    """
    root = memory_copy(tmp_path)
    memory = root / "memory"
    real = next(path for path in sorted(memory.glob("*.md")) if path.name != "MEMORY.md")
    (memory / "INDEX_probe.md").write_text(
        f"# Probe index\n\n- [A real leaf]({real.name}) - resolves.\n",
        encoding="utf-8",
        newline="\n",
    )
    index = memory / "MEMORY.md"
    index.write_text(
        index.read_text(encoding="utf-8") + "\n- [Probe](INDEX_probe.md) - a child index.\n",
        encoding="utf-8",
        newline="\n",
    )

    status, rendered = memory_verdict(root)
    assert status == "PASS", (
        f"a child index whose every link resolves was reported as drift:\n{rendered}"
    )


def test_a_fragment_and_an_extensionless_link_are_not_reported_as_missing(
    tmp_path: Path,
) -> None:
    """Two shapes that cite a real target without spelling it as a path.

    A bare ``#anchor`` points inside the citing file, and a link written
    without the ``.md`` is how a wikilink-shaped target reads in markdown
    syntax. Neither is a broken citation and neither may be reported as one -
    the store uses neither today, so nothing else here would notice.
    """
    root = memory_copy(tmp_path)
    memory = root / "memory"
    leaf = next(path for path in sorted(memory.glob("*.md")) if path.name != "MEMORY.md")
    other = next(
        path for path in sorted(memory.glob("*.md")) if path.name not in {"MEMORY.md", leaf.name}
    )

    before = leaf.read_text(encoding="utf-8")
    after = (
        f"{before}\nSee [the section above](#how-to-work) and "
        f"[the other note]({other.stem}) for the rest.\n"
    )
    assert after != before, "the plant did not apply"
    leaf.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = memory_verdict(root)
    assert status == "PASS", (
        f"a bare fragment or an extensionless link was reported as missing:\n{rendered}"
    )


# ---------------------------------------------------------------------------
# THE TWO DEFECTS A PARITY TOGGLE COULD NOT SEE
# ---------------------------------------------------------------------------
# The first repair of this guard detected fences by flipping a boolean on any
# line whose first run was three or more backticks. Both arms below were RED
# (G1) or manufactured (F1) under that scheme, and neither was caught by the
# several hundred test lines above it - because the fence pattern in this
# module was a VERBATIM COPY of the guard's own, so the oracle carried the
# same defect as the thing it was grading. The scanner those arms now use is
# written character by character instead.


def test_two_prose_lines_starting_with_a_fence_do_not_swallow_the_file(
    tmp_path: Path,
) -> None:
    """G1 - THE SILENT GREEN, and the reason parity was never a safety net.

    Two ORDINARY PROSE lines that merely begin with three backticks give EVEN
    parity. Under the toggle, everything between them was blanked, the guard
    returned PASS, the population line was byte-identical to pristine, and no
    skip of any kind fired - while the store held two dangling wikilinks. The
    odd-parity net could not cover the case that actually swallows, because
    swallowing does not require an unclosed fence.

    Under CommonMark the first of those lines opens a fence with an info
    string and the second cannot close it, since a closer carries none. So the
    file ends with a fence open, and THAT is what must be reported.
    """
    root = memory_copy(tmp_path)
    leaf = next(path for path in sorted((root / "memory").glob("*.md")) if path.name != "MEMORY.md")
    assert not (root / "memory" / f"{GHOST_LEAF}.md").exists(), "the plant names a real file"

    before = leaf.read_text(encoding="utf-8")
    after = (
        f"{before}\n``` is how you open a fence in markdown.\n"
        f"\nSee [[{GHOST_LEAF}]] and [[{GHOST_LEAF}-two]] for the rest.\n"
        f"\n``` is also how you close one.\n"
    )
    assert after != before, "the plant did not apply"
    leaf.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = memory_verdict(root)
    assert status == "FAIL", (
        "two prose lines beginning with a fence swallowed the text between them and the "
        f"guard reported {status} over a region it never read:\n{rendered}"
    )
    assert leaf.name in rendered, "the guard failed without naming the file that went unread"


def test_a_four_backtick_fence_wrapping_an_example_is_not_a_finding(tmp_path: Path) -> None:
    """F1 - THE MANUFACTURED FINDING, on content this store already carries.

    Documenting a fence means wrapping it in a longer one. The toggle
    un-toggled on the inner three-backtick opener, so the example body was
    read as prose and the guard went FAIL on ``[[tool.mypy.overrides]]``.

    That block is not hypothetical: ``a-guard-can-be-accepted-and-unscoped.md``
    already carries it inside a plain three-backtick fence, in a store whose
    whole subject is how guards fail. A note quoting it would have reddened
    guard (b) and blocked every commit and push in the repository - which is
    the precise harm the narrower extractor was introduced to avoid.
    """
    root = memory_copy(tmp_path)
    leaf = next(path for path in sorted((root / "memory").glob("*.md")) if path.name != "MEMORY.md")
    before = leaf.read_text(encoding="utf-8")
    after = (
        f"{before}\nTo document a fence, wrap it in a longer one:\n\n"
        f"````\n```\n[[tool.mypy.overrides]]\nignore_missing_imports = true\n```\n````\n"
    )
    assert after != before, "the plant did not apply"
    leaf.write_text(after, encoding="utf-8", newline="\n")

    status, rendered = memory_verdict(root)
    assert status == "PASS", (
        "a three-backtick example inside a four-backtick fence was read as prose, so the "
        f"guard manufactured a finding on correct content:\n{rendered}"
    )


def test_the_reported_population_matches_an_independently_derived_count(
    tmp_path: Path,
) -> None:
    """The counts guard (b) prints are CHECKED, not decorated.

    The floor this replaces asked only that the store hold at least one
    wikilink and at least one markdown link. One of each satisfies that, so a
    guard whose extractor had collapsed to almost nothing would still have
    passed while printing "60 of 60" - the number was never compared to
    anything.

    THE ORACLE OWES NOTHING TO A CODE MODEL, which is the second thing that
    was wrong here. The counts are a naive scan of the raw bytes minus a
    HAND-ENUMERATED list of tokens that sit inside code. The version this
    replaces derived them with a line-for-line clone of the guard's own
    scanner, so it agreed with the guard on every pathology by construction
    and could not have caught one.

    Equality is asserted rather than a literal 20 and 60, because a hardcoded
    count is a lie with a timestamp on it the moment a note is added. The
    floor below is structural for the same reason: the index links every leaf,
    so its population cannot be smaller than the number of leaves.
    """
    root = memory_copy(tmp_path)
    memory = root / "memory"
    leaves = [path for path in memory.glob("*.md") if path.name != "MEMORY.md"]
    index_expected, leaf_expected = expected_citation_counts(memory)

    assert index_expected >= len(leaves), (
        f"the index cites {index_expected} targets for {len(leaves)} leaves, so it cannot "
        "be linking them all and this control is grading a broken store"
    )
    assert leaf_expected >= len(leaves), (
        f"only {leaf_expected} leaf citations across {len(leaves)} leaves - too thin a "
        "population for a green about cross-referencing to mean anything"
    )

    status, rendered = memory_verdict(root)
    assert status == "PASS", f"the tracked store is not clean:\n{rendered}"

    index_reported, leaf_reported = reported_citation_counts(rendered)
    assert index_reported == index_expected, (
        f"guard (b) says it checked {index_reported} index citations; an independent scan "
        f"finds {index_expected}. The printed population is not the real one."
    )
    assert leaf_reported == leaf_expected, (
        f"guard (b) says it checked {leaf_reported} leaf citations; an independent scan "
        f"finds {leaf_expected}. The printed population is not the real one."
    )


# ---------------------------------------------------------------------------
# CODE SHAPES - WHAT IS EXCLUDED, AND WHAT IS A RECORDED RESIDUAL
# ---------------------------------------------------------------------------
# The exclusion was spelled "fenced code" when the property it needs is CODE,
# and the name is what let the gap hide: inline spans were not excluded at
# all, so one line of ordinary prose quoting a TOML header turned guard (b)
# FAIL. Before this section existed, ``grep -c inline`` over this module
# returned ZERO - there was no arm for an inline span, an indented code block,
# a blockquote or a list item anywhere in it.
#
# THE THREE RESIDUAL ARMS BELOW ASSERT THE WRONG-BUT-CURRENT BEHAVIOUR ON
# PURPOSE. The model is line-oriented and has no container model, so a fence
# inside a list item or a blockquote, and a four-space indented code block,
# are all still read as prose. Guessing at a container model would trade this
# LOUD failure for a SILENT one - a wikilink wrongly treated as code is a
# dangling citation nobody is told about, which is the G1 class this whole
# item exists to close. So they are pinned rather than fixed: when someone
# does fix one, its arm fails and forces this table to be updated with it.


def plant(root: Path, addition: str) -> Path:
    """Append ``addition`` to the first ordinary leaf of a copied store.

    Args:
        root: The fake repository root from ``memory_copy``.
        addition: Markdown to append.

    Returns:
        The leaf that was written.
    """
    leaf = next(path for path in sorted((root / "memory").glob("*.md")) if path.name != "MEMORY.md")
    before = leaf.read_text(encoding="utf-8")
    after = before + addition
    assert after != before, "the plant did not apply"
    leaf.write_text(after, encoding="utf-8", newline="\n")
    return leaf


def test_an_inline_code_span_is_not_a_citation(tmp_path: Path) -> None:
    """P5 - one line of ORDINARY PROSE used to turn guard (b) FAIL.

    Not a hypothetical shape. ``MEMORY.md`` already writes `assert count == 0`
    and `git commit -F` in inline spans; ``tools/drift_guard.py`` carries this
    very token twice in its own docstrings; and CS-890's lesson is a likely
    new memory leaf whose natural phrasing quotes it inline. The next note
    that did would have reddened guard (b) and blocked every commit and push
    in the repository.
    """
    root = memory_copy(tmp_path)
    plant(root, "\nThe TOML header `[[tool.mypy.overrides]]` is spelled like a wikilink.\n")

    status, rendered = memory_verdict(root)
    assert status == "PASS", f"an inline code span was resolved as a citation:\n{rendered}"


def test_a_multi_backtick_inline_span_is_not_a_citation(tmp_path: Path) -> None:
    """A span opens on N backticks and closes on exactly N, per CommonMark.

    The double-backtick form is how a span containing a backtick is written,
    so an implementation that only understood a single delimiter would pass
    the arm above and still be wrong.
    """
    root = memory_copy(tmp_path)
    plant(root, "\nA span written ``[[tool.mypy.overrides]]`` holds the token.\n")

    status, rendered = memory_verdict(root)
    assert status == "PASS", (
        f"a double-backtick inline span was resolved as a citation:\n{rendered}"
    )


def test_a_dangling_wikilink_beside_an_inline_span_still_reddens(tmp_path: Path) -> None:
    """The span exclusion is scoped to the span, not to the line holding it.

    Without this control, blanking the whole line on sight would pass both
    arms above while quietly dropping every citation that shares a line with
    any code.
    """
    root = memory_copy(tmp_path)
    plant(root, f"\nSee [[{GHOST_LEAF}]] - the header is `[[tool.mypy.overrides]]`.\n")

    status, rendered = memory_verdict(root)
    assert status == "FAIL", (
        "a dangling wikilink sharing a line with an inline span was excluded with it "
        f"and the guard said {status}:\n{rendered}"
    )
    assert GHOST_LEAF in rendered, "the guard failed without naming the dangling target"


def test_a_fence_closed_at_a_deeper_indent_than_it_opened(tmp_path: Path) -> None:
    """P3 - a regression the previous repair introduced, and worse than a skip.

    A fence opened at two spaces and closed at four is what a fence inside a
    list item looks like when the closer carries the item's indent. Applying
    CommonMark's three-space cap to the CLOSER made it read as unterminated,
    which under the new failure rule BLOCKED THE COMMIT - F1's mistake with
    the opposite sign. The cap is now applied to openers only, which errs
    toward closing a fence and so cannot swallow a file.
    """
    root = memory_copy(tmp_path)
    plant(root, "\n  ```\n  [[tool.mypy.overrides]]\n    ```\n")

    status, rendered = memory_verdict(root)
    assert status == "PASS", (
        f"a fence whose closer was indented further than its opener was read as "
        f"unterminated and failed the commit:\n{rendered}"
    )


def test_a_fence_inside_a_nested_list_item_is_recognised(tmp_path: Path) -> None:
    """P1 - was a pinned residual, fixed by CS-895's container model.

    The fence is indented four spaces because it sits in a nested list item.
    A line-oriented model measures that four against the document margin, past
    the three-space opener cap, so the fence never opened and the token inside
    was read as prose and reported as a dangling citation. The indent is now
    measured against the ENCLOSING ITEM'S CONTENT COLUMN, where it is zero.
    """
    root = memory_copy(tmp_path)
    plant(root, "\n- outer\n  - inner\n\n    ```\n    [[tool.mypy.overrides]]\n    ```\n")

    status, rendered = memory_verdict(root)
    assert status == "PASS", f"a fence inside a nested list item was not recognised:\n{rendered}"


def test_a_fence_inside_a_blockquote_is_recognised(tmp_path: Path) -> None:
    """P2 - was a pinned residual, fixed by CS-895's container model.

    Every line carries a "> " prefix, so the fence never started its line and
    was never seen. Blockquote markers are now stripped before the fence scan.
    """
    root = memory_copy(tmp_path)
    plant(root, "\n> quoting a note:\n>\n> ```\n> [[tool.mypy.overrides]]\n> ```\n")

    status, rendered = memory_verdict(root)
    assert status == "PASS", f"a fence inside a blockquote was not recognised:\n{rendered}"


def test_a_four_space_indented_code_block_is_recognised(tmp_path: Path) -> None:
    """P4 - was a pinned residual, fixed by CS-895's container model.

    An indented code block uses no fence at all, so nothing in a fence-only
    model could ever see it. It is now recognised by indent measured against
    the enclosing container, which is what keeps it distinct from list
    content - see the control below, which is the half that goes SILENTLY
    wrong if it is guessed at.
    """
    root = memory_copy(tmp_path)
    plant(
        root,
        "\nAn indented code block:\n\n    [[tool.mypy.overrides]]\n    key = 1\n\nBack to prose.\n",
    )

    status, rendered = memory_verdict(root)
    assert status == "PASS", f"an indented code block was not recognised:\n{rendered}"


# --- the anti-vacuity controls for the three above --------------------------
#
# Each arm above is satisfied by BLANKING MORE, and blanking more is the
# failure direction that is silent: a citation dropped on the floor is a
# dangling link nobody is told about. Every control below plants a DANGLING
# target in a position the exclusion must not reach, and asserts the guard
# still reddens AND still names it.


def test_four_spaces_inside_a_list_item_is_content_and_not_a_code_block(
    tmp_path: Path,
) -> None:
    """THE CONTROL P4's RESIDUAL DOCSTRING NAMED AS THE SILENT WAY TO GET IT WRONG.

    Four spaces from the margin is an indented code block at top level and is
    ordinary CONTENT inside a list item whose marker put the content column at
    two. A model measuring indent against the document margin excludes this
    citation and reports PASS over a dangling link. There is no loud failure
    to notice afterwards, which is why this arm exists.
    """
    root = memory_copy(tmp_path)
    plant(root, f"\n- outer\n\n    See [[{GHOST_LEAF}]] - still item content.\n")

    status, rendered = memory_verdict(root)
    assert status == "FAIL", (
        "four-space-indented text inside a list item was excluded as a code block "
        f"and the guard said {status}:\n{rendered}"
    )
    assert GHOST_LEAF in rendered, "the guard failed without naming the dangling target"


def test_an_indented_line_may_not_interrupt_a_paragraph(tmp_path: Path) -> None:
    """An indented code block cannot start inside a paragraph, per CommonMark.

    Without the blank-line requirement, any wrapped prose line a writer happens
    to indent becomes code and its citations vanish. The plant is one paragraph
    whose second line is indented four spaces.
    """
    root = memory_copy(tmp_path)
    plant(root, f"\nA paragraph runs on\n    and cites [[{GHOST_LEAF}]] on its indented line.\n")

    status, rendered = memory_verdict(root)
    assert status == "FAIL", (
        "an indented continuation line interrupted a paragraph as a code block "
        f"and the guard said {status}:\n{rendered}"
    )
    assert GHOST_LEAF in rendered, "the guard failed without naming the dangling target"


def test_a_dangling_link_beside_a_blockquote_fence_still_reddens(tmp_path: Path) -> None:
    """The blockquote exclusion is scoped to the fence, not to the quote.

    Blanking every line carrying a "> " prefix would pass P2's arm above and
    drop every citation any quoted note ever makes.
    """
    root = memory_copy(tmp_path)
    plant(
        root,
        f"\n> quoting a note that cites [[{GHOST_LEAF}]]:\n>\n"
        "> ```\n> [[tool.mypy.overrides]]\n> ```\n",
    )

    status, rendered = memory_verdict(root)
    assert status == "FAIL", (
        f"a dangling wikilink in blockquote PROSE was excluded with the quoted fence "
        f"and the guard said {status}:\n{rendered}"
    )
    assert GHOST_LEAF in rendered, "the guard failed without naming the dangling target"


def test_a_dangling_link_in_a_list_item_beside_a_fence_still_reddens(tmp_path: Path) -> None:
    """The list-item exclusion is scoped to the fence, not to the item.

    Blanking an item on sight of a fence anywhere in it would pass P1's arm
    above and drop the citations of every list that quotes code.
    """
    root = memory_copy(tmp_path)
    plant(
        root,
        f"\n- outer\n  - inner cites [[{GHOST_LEAF}]]\n\n"
        "    ```\n    [[tool.mypy.overrides]]\n    ```\n",
    )

    status, rendered = memory_verdict(root)
    assert status == "FAIL", (
        f"a dangling wikilink in list-item PROSE was excluded with the item's fence "
        f"and the guard said {status}:\n{rendered}"
    )
    assert GHOST_LEAF in rendered, "the guard failed without naming the dangling target"


def test_a_list_item_closes_its_containers_when_the_indent_falls_back(tmp_path: Path) -> None:
    """A container's columns must not outlive it, or the margin drifts right.

    After a nested item at content column four, prose returning to the margin
    is outside both items. A model that never popped its column stack would
    keep measuring against four and would read this top-level indented block
    as ordinary prose - or, with the sign the other way, read margin prose as
    code. The plant returns to the margin and then cites a ghost.
    """
    root = memory_copy(tmp_path)
    plant(
        root,
        "\n- outer\n  - inner\n\n    ```\n    [[tool.mypy.overrides]]\n    ```\n\n"
        f"Back at the margin, [[{GHOST_LEAF}]].\n",
    )

    status, rendered = memory_verdict(root)
    assert status == "FAIL", (
        f"a citation at the margin after a nested list was lost with the list "
        f"and the guard said {status}:\n{rendered}"
    )
    assert GHOST_LEAF in rendered, "the guard failed without naming the dangling target"


# ---------------------------------------------------------------------------
# CS-910 - what this guard actually hands to the spawn
# ---------------------------------------------------------------------------


def test_the_git_this_guard_spawns_is_resolved_and_never_named(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """CS-910 - a RUNTIME reading, alongside the static census in test_toolpath.

    A bare ``"git"`` in an argv is resolved by ``CreateProcess``, which searches
    the CURRENT DIRECTORY before PATH whenever the gate variable is absent from
    the environment - its state at both machine and user scope on the development
    machine. This guard is deliberately POINTED AT TREES IT DID NOT CREATE, which
    makes the directory it stands in someone else's, and it is what decides which
    files every other guard here is run over.

    NOTHING BELOW ASSERTS ON A PATH. Every assertion binds a boolean.
    """
    recorded: list[list[str]] = []

    def record(argv: list[str], **_kwargs: object) -> Any:
        recorded.append(list(argv))
        return drift_guard.subprocess.CompletedProcess(list(argv), 0, "", "")

    monkeypatch.setattr(drift_guard.subprocess, "run", record)
    drift_guard._git_ls_files(tmp_path)  # noqa: SLF001 - the site under test

    assert len(recorded) == 1, "the guard did not spawn exactly once, so this grades nothing"
    program = recorded[0][0]
    rooted = Path(program).is_absolute()
    assert rooted, "the program handed to the spawn is not an absolute path"
    named = program == drift_guard.GIT_NAME
    assert not named, "the program handed to the spawn is the bare tool name"


def test_an_unresolvable_git_yields_no_files_rather_than_spawning(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """CS-910 - the refusal path.

    A resolver that finds nothing must stop the spawn rather than fall back to
    the name, since falling back is the behaviour being removed. The empty list
    it answers with is what a git that FAILS already answers here.
    """
    spawned: list[object] = []

    def record(argv: object, **_kwargs: object) -> None:
        spawned.append(argv)

    monkeypatch.setattr(drift_guard, "resolve_tool", lambda _name: None)
    monkeypatch.setattr(drift_guard.subprocess, "run", record)

    answer = drift_guard._git_ls_files(tmp_path)  # noqa: SLF001 - the site under test

    assert answer == []
    assert spawned == [], "the guard spawned something after the resolver refused"


# ---------------------------------------------------------------------------
# CS-1113 (b) - a WARN that means "could not look" is never CLEAN
# ---------------------------------------------------------------------------
#
# A WARN carried two meanings and the overall verdict read them as one: a soft
# finding on input that WAS read (a doc over its soft budget, a port with no
# record) and an input that was never read at all. As the only non-PASS guard,
# either one left the exit code 0 and the JSON verdict CLEAN - the
# could-not-look-reads-as-clean class. The meaning is now an explicit flag SET AT
# THE WARN SITE: ``advisory`` is an allowlist of the soft findings, and every
# other WARN makes the run UNGRADED with a non-zero exit code. A text match on a
# detail message is never how the two are told apart.
#
# EVERY PLANT BELOW IS THE ONLY NON-PASS GUARD ON ITS TREE, and the arm asserts
# that before it asserts the verdict. A plant that also reddened a second guard
# would make a non-zero exit code a statement about that guard instead. The
# exceptions are named in ALSO_UNGRADED: a removed memory index is ALSO a budgeted
# file guard (a) could not measure (CS-1115), an unreadable markdown file is ALSO
# unread by guards (c), (g) and (k) (CS-1117), and every WARN is asserted
# non-advisory, so none can carry the verdict for another.

#: Every guard the driver registers. Spelled out so a guard that silently drops
#: out of the run is a red floor rather than one fewer thing that has to PASS.
ALL_GUARD_IDS = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k"]


def swap_for_directory(path: Path) -> None:
    """Replace a file with a directory of the same name, so reading it raises.

    The adversary on CS-1086 made ROADMAP.md unreadable this way; a directory
    raises OSError on read on every platform, where a permission bit does not.

    Args:
        path: The file to swap.
    """
    path.unlink()
    path.mkdir()
    assert path.is_dir(), "the swap did not apply, so nothing was made unreadable"


def non_pass(report: dict[str, Any]) -> dict[str, str]:
    """Return guard id mapped to status for every guard that did not PASS.

    Args:
        report: The parsed JSON report.

    Returns:
        The non-PASS guards.
    """
    return {guard["id"]: guard["status"] for guard in report["guards"] if guard["status"] != "PASS"}


def _plant_memory_absent(root: Path, _monkeypatch: pytest.MonkeyPatch) -> None:
    shutil.rmtree(root / "memory")


def _plant_memory_index_absent(root: Path, _monkeypatch: pytest.MonkeyPatch) -> None:
    (root / "memory" / "MEMORY.md").unlink()


def _plant_conventions_unparseable(root: Path, _monkeypatch: pytest.MonkeyPatch) -> None:
    (root / "CONVENTIONS.md").write_text("# Fake conventions, no section 2\n", encoding="utf-8")


def _plant_no_frozen_section(root: Path, _monkeypatch: pytest.MonkeyPatch) -> None:
    claude = root / "CLAUDE.md"
    text = claude.read_text(encoding="utf-8")
    cut = text.split("## 6. Frozen files")[0]
    assert cut != text, "the frozen section was not removed, so this plants nothing"
    claude.write_text(cut, encoding="utf-8")


def _plant_pin_absent(root: Path, _monkeypatch: pytest.MonkeyPatch) -> None:
    pin_path(root).unlink()


def _plant_pin_not_importable(_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse() -> Any:
        message = "a synthetic import failure"
        raise ImportError(message)

    monkeypatch.setattr(drift_guard, "_load_pin_support", refuse)


def _plant_no_owner_declaration(root: Path, _monkeypatch: pytest.MonkeyPatch) -> None:
    (root / "CLAUDE.md").write_text(_CLAUDE_MD, encoding="utf-8")


def _plant_owner_files_empty(root: Path, _monkeypatch: pytest.MonkeyPatch) -> None:
    for relative in WORK_ITEM_OWNERS.values():
        (root / relative).write_text("# nothing here\n", encoding="utf-8")


def _plant_index_unreadable(
    root: Path, _monkeypatch: pytest.MonkeyPatch
) -> contextlib.AbstractContextManager[None]:
    # CS-1117 - a REAL read fault, held for the run. A directory swapped in
    # under the index's name is now guard (a)'s NOT A FILE FAIL, a different
    # defect, so it can no longer stand in for an unreadable file.
    return refused(root / ITEM_NOTES_INDEX_RELATIVE)


def _plant_leaf_directory_absent(root: Path, _monkeypatch: pytest.MonkeyPatch) -> None:
    shutil.rmtree(root / ITEM_NOTES_LEAF_RELATIVE.rsplit("/", 1)[0])


def _plant_empty_family(root: Path, _monkeypatch: pytest.MonkeyPatch) -> None:
    (root / ROADMAP_RELATIVE).write_text("# Fake roadmap, nothing routed\n", encoding="utf-8")
    (root / ITEM_NOTES_INDEX_RELATIVE).write_text("# Fake index, no rows\n", encoding="utf-8")
    (root / ITEM_NOTES_LEAF_RELATIVE).write_text("# Fake leaf, no sections\n", encoding="utf-8")


def _plant_roadmap_unreadable(
    root: Path, _monkeypatch: pytest.MonkeyPatch
) -> contextlib.AbstractContextManager[None]:
    # CS-1117 - a real read fault, for the reason given on the index plant.
    return refused(root / ROADMAP_RELATIVE)


def _plant_workflow_absent(root: Path, _monkeypatch: pytest.MonkeyPatch) -> None:
    (root / TIER1_WORKFLOW_RELATIVE).unlink()


def _plant_nothing_enumerated(_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(drift_guard, "enumerate_files", lambda _root: ([], "no files", []))


def _plant_budgeted_file_absent(root: Path, _monkeypatch: pytest.MonkeyPatch) -> None:
    (root / UPSTREAM_WATCH_RELATIVE).unlink()


#: One plant per could-not-look WARN site the driver can reach with no other
#: guard going non-PASS, keyed by the guard it makes WARN. A plant returns the
#: context manager holding its fault when the fault is a live handle (CS-1117).
COULD_NOT_LOOK_PLANTS: dict[
    str,
    tuple[
        str, Callable[[Path, pytest.MonkeyPatch], contextlib.AbstractContextManager[None] | None]
    ],
] = {
    "a-budgeted-file-absent": ("a", _plant_budgeted_file_absent),
    "b-memory-absent": ("b", _plant_memory_absent),
    "b-memory-index-absent": ("b", _plant_memory_index_absent),
    "c-nothing-checked": ("c", _plant_nothing_enumerated),
    "d-conventions-unparseable": ("d", _plant_conventions_unparseable),
    "f-no-frozen-section": ("f", _plant_no_frozen_section),
    "h-pin-absent": ("h", _plant_pin_absent),
    "h-pin-not-importable": ("h", _plant_pin_not_importable),
    "i-no-owner-declaration": ("i", _plant_no_owner_declaration),
    "i-owner-files-empty": ("i", _plant_owner_files_empty),
    "j-index-unreadable": ("j", _plant_index_unreadable),
    "j-leaf-directory-absent": ("j", _plant_leaf_directory_absent),
    "j-empty-family": ("j", _plant_empty_family),
    "j-roadmap-unreadable": ("j", _plant_roadmap_unreadable),
    "k-workflow-absent": ("k", _plant_workflow_absent),
}

#: CS-1115 - the plants that ALSO leave a budgeted file unmeasured, so guard (a)
#: is a second could-not-look WARN on the same tree. Named per plant, so any
#: OTHER guard joining a plant's run is still red, and both flags are asserted.
#:
#: CS-1117 - and the plants that hold a REAL read fault on a markdown file, which
#: guards (c), (g) and (k) each read and now each report as could-not-look. No
#: FAIL joins them, so the verdict still rests on the non-advisory flag alone.
ALSO_UNGRADED = {
    "b-memory-absent": ["a"],
    "b-memory-index-absent": ["a"],
    "j-index-unreadable": ["c", "g", "k"],
    "j-roadmap-unreadable": ["c", "g", "k"],
}

#: The readers of one refused markdown file on the base fixture (CS-1117).
MARKDOWN_READERS = ["c", "g", "j", "k"]


def test_the_base_fixture_passes_every_guard_and_is_clean(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The floor under every plant below: nothing is non-PASS before planting.

    Without it, a plant's non-zero exit code could belong to a guard the
    fixture never satisfied.
    """
    code, report = run_main(capsys)
    assert [guard["id"] for guard in report["guards"]] == ALL_GUARD_IDS
    assert non_pass(report) == {}, report["guards"]
    assert (report["verdict"], code) == ("CLEAN", 0)
    assert report["ungraded"] == []
    assert (repo / ROADMAP_RELATIVE).is_file()


def test_an_unreadable_roadmap_warns_all_four_markdown_readers_and_is_not_clean(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CS-1113 acceptance arm, through main() on BOTH output paths.

    ROADMAP.md is made unreadable and no guard FAILS, so its four could-not-look
    WARNs are the only non-PASS guards on the tree - CS-1120 renamed the arm,
    whose old name still said guard (j) was the ONLY one. CS-1117: that is no longer guard
    (j) alone - (c), (g) and (k) read the same file and now say so - and the
    fault is a REAL exclusive handle, because a directory swapped in under the
    name is guard (a)'s NOT A FILE FAIL, which would carry the verdict itself.
    """
    with refused(repo / ROADMAP_RELATIVE):
        code, report = run_main(capsys)
        text_code = drift_guard.main([])
        printed = capsys.readouterr().out.splitlines()

    assert non_pass(report) == dict.fromkeys(MARKDOWN_READERS, "WARN"), report["guards"]
    assert report["verdict"] == "UNGRADED"
    assert code != 0, "a run that could not read ROADMAP.md exited 0"
    assert report["ungraded"] == MARKDOWN_READERS
    assert report["drift"] == []
    for each in MARKDOWN_READERS:
        assert guard_of(report, each)["advisory"] is False, each

    verdicts = [line for line in printed if line.startswith("VERDICT:")]
    assert text_code != 0, "the text path exited 0 over an unread ROADMAP.md"
    assert len(verdicts) == 1, verdicts
    assert verdicts[0].startswith("VERDICT: UNGRADED"), verdicts


@pytest.mark.parametrize("plant", sorted(COULD_NOT_LOOK_PLANTS))
def test_every_could_not_look_warn_makes_the_run_ungraded(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], plant: str
) -> None:
    """The sibling sweep: every WARN site meaning "never read" blocks CLEAN."""
    guard_id, apply = COULD_NOT_LOOK_PLANTS[plant]
    expected = sorted([guard_id, *ALSO_UNGRADED.get(plant, [])])

    with contextlib.ExitStack() as held:
        fault = apply(repo, monkeypatch)
        if fault is not None:
            held.enter_context(fault)
        code, report = run_main(capsys)
    assert non_pass(report) == dict.fromkeys(expected, "WARN"), report["guards"]
    assert report["verdict"] == "UNGRADED"
    assert code != 0
    assert sorted(report["ungraded"]) == expected
    for each in expected:
        assert guard_of(report, each)["advisory"] is False, each


@pytest.mark.parametrize("site", ["absent", "unreadable"])
def test_the_frozen_guard_could_not_look_sites_are_not_advisory(repo: Path, site: str) -> None:
    """Guard (f)'s two sites a driver-level plant cannot isolate.

    Removing CLAUDE.md also reddens guard (d), whose ownership table names it,
    so these two are graded at the guard: the flag is what the driver reads.
    """
    claude = repo / "CLAUDE.md"
    if site == "absent":
        claude.unlink()
    else:
        swap_for_directory(claude)

    guard, _skips = drift_guard.guard_frozen(repo)
    assert guard["status"] == "WARN", guard["detail"]
    assert guard["advisory"] is False


# --- CS-1115 - guard (a) measured every budgeted file, or says which it did not


def test_an_absent_budgeted_file_is_named_and_never_advisory(repo: Path) -> None:
    """A budgeted file that must exist and does not was never measured.

    Guard (a) used to put it on the skip list and PASS, while its advisory
    comment claimed every budgeted file was MEASURED. Guard (f), (b) and (j)
    happen to catch CLAUDE.md, MEMORY.md, ROADMAP.md and the index going
    missing, but nothing else reads docs/upstream_watch.md - so the fixture
    below was a clean run over a file nobody had measured.
    """
    (repo / UPSTREAM_WATCH_RELATIVE).unlink()

    guard, skips = drift_guard.guard_budgets(repo)
    rendered = "\n".join(guard["detail"])
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert UPSTREAM_WATCH_RELATIVE in rendered, rendered
    assert any(skip["path"] == UPSTREAM_WATCH_RELATIVE for skip in skips), skips


def test_an_absent_budgeted_file_beside_a_soft_overshoot_is_still_not_advisory(
    repo: Path,
) -> None:
    """A soft finding on another file must not launder the unmeasured one."""
    _plant_roadmap_over_its_soft_budget(repo)
    (repo / UPSTREAM_WATCH_RELATIVE).unlink()

    guard, _skips = drift_guard.guard_budgets(repo)
    rendered = "\n".join(guard["detail"])
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert ROADMAP_RELATIVE in rendered, "the soft overshoot vanished from the detail"


def test_an_absent_measured_when_present_file_is_not_a_finding(repo: Path) -> None:
    """The control: CLAUDE.local.md is budgeted only WHEN PRESENT, by doc_budget's own rule.

    The real tree and a fresh clone both lack it, so reporting its absence as
    could-not-look would make every CI run UNGRADED.
    """
    doc_budget = drift_guard._load_doc_budget()  # noqa: SLF001 - the budget's own owner
    optional = "CLAUDE.local.md"
    assert optional in doc_budget.AUTOLOADED_EXPLICIT, "the control names no budgeted file"
    assert not (repo / optional).exists(), "control: the fixture carries the optional file"

    guard, skips = drift_guard.guard_budgets(repo)
    assert guard["status"] == "PASS", guard["detail"]
    assert any(skip["path"] == optional for skip in skips), skips


def test_a_present_but_unmeasurable_optional_file_is_not_advisory(repo: Path) -> None:
    """Present-but-unmeasurable is not absent: a dangling link stats as missing, lstats as there."""
    optional = repo / "CLAUDE.local.md"
    try:
        optional.symlink_to(repo / "a-target-that-does-not-exist.md")
    except OSError as exc:
        pytest.skip(f"this account cannot create a symbolic link: {exc.strerror}")
    assert optional.is_symlink(), "control: the link was not created"
    assert not optional.exists(), "control: the link is not dangling"

    guard, _skips = drift_guard.guard_budgets(repo)
    rendered = "\n".join(guard["detail"])
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert "CLAUDE.local.md" in rendered, rendered


# --- CS-1115 - an item-notes leaf or leaf directory that EXISTS but cannot be read


@pytest.mark.parametrize("target", ["leaf", "leaf-directory"])
def test_a_refused_item_notes_read_makes_the_run_ungraded(
    repo: Path, capsys: pytest.CaptureFixture[str], target: str
) -> None:
    """A real read fault under docs/item_notes/ is could-not-look, through main().

    Before CS-1115 the leaf was skipped silently and its routed item read as a
    row with no section - a FAIL naming the wrong defect. The directory case
    was the same shape one level up: a refused listing globbed as zero leaves.
    """
    leaf = repo / ITEM_NOTES_LEAF_RELATIVE
    path = leaf if target == "leaf" else leaf.parent
    named = path.relative_to(repo).as_posix()

    with refused(path):
        assert leaf.parent.is_dir(), "control: the leaf directory no longer stats"
        if target == "leaf":
            assert leaf.is_file(), "control: the refused leaf no longer stats as a file"
            with pytest.raises(PermissionError):
                leaf.read_bytes()
        else:
            with pytest.raises(PermissionError):
                list(path.iterdir())
        code, report = run_main(capsys)

    # A refused DIRECTORY also hides the leaves guard (a) budgets, so guard (a)
    # is a second could-not-look WARN there; a refused leaf still stats. A
    # refused LEAF is a markdown file guards (c), (g) and (k) read (CS-1117).
    # CS-1120: the walk hands a directory it cannot list to (c), (g) and (k)
    # too, so the refused directory is NOT LISTED to all three.
    expected = MARKDOWN_READERS if target == "leaf" else ["a", "c", "g", "j", "k"]
    assert non_pass(report) == dict.fromkeys(expected, "WARN"), report["guards"]
    assert report["verdict"] == "UNGRADED"
    assert code != 0, "a run that could not read the item-notes family exited 0"
    assert sorted(report["ungraded"]) == expected
    for each in expected:
        assert guard_of(report, each)["advisory"] is False, each
    guard = guard_of(report, "j")
    # The path AND the verdict word, never the path alone: "docs/item_notes"
    # is a prefix of the index path every detail block already prints.
    assert any(f"{named} NOT READ" in line for line in guard["detail"]), guard["detail"]


def test_a_refused_item_notes_directory_makes_guard_a_itself_warn(repo: Path) -> None:
    """Guard (a) on its own, so guard (j) cannot be what saves the verdict."""
    leaf_dir = repo / ITEM_NOTES_LEAF_RELATIVE.rsplit("/", 1)[0]

    with refused(leaf_dir):
        guard, skips = drift_guard.guard_budgets(repo)

    rendered = "\n".join(guard["detail"])
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert "NOT LISTED docs/item_notes/" in rendered, rendered
    assert any(skip["path"] == "docs/item_notes/" for skip in skips), skips


def test_a_refused_memory_directory_makes_the_run_ungraded(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Guard (b) never reports ``leaves: 0`` PASS over a store it could not list.

    Guard (a) loses the same leaves, so both WARN, and neither is advisory.
    CS-1120: the walk hands the unlisted store to (c), (g) and (k), which WARN too.
    """
    memory = repo / "memory"
    (memory / "a-leaf.md").write_text("# A leaf\n", encoding="utf-8")
    index = memory / "MEMORY.md"
    index.write_text(index.read_text(encoding="utf-8") + "- [A leaf](a-leaf.md)\n", "utf-8")
    code, report = run_main(capsys)
    assert (report["verdict"], code) == ("CLEAN", 0), "control: the leaf tree is not clean"

    with refused(memory):
        assert memory.is_dir(), "control: the refused store no longer stats"
        with pytest.raises(PermissionError):
            list(memory.iterdir())
        code, report = run_main(capsys)

    expected = ["a", "b", "c", "g", "k"]
    assert non_pass(report) == dict.fromkeys(expected, "WARN"), report["guards"]
    assert report["verdict"] == "UNGRADED"
    assert code != 0
    for each in expected:
        assert guard_of(report, each)["advisory"] is False, each
    for each in ("c", "g", "k"):
        assert "memory/ NOT LISTED" in _detail(guard_of(report, each)), each
    detail = guard_of(report, "b")["detail"]
    assert "memory/ NOT LISTED" in "\n".join(detail), detail


def test_a_refused_frozen_glob_directory_is_not_a_pass(repo: Path) -> None:
    """Guard (f) globbed `.githooks/*` and a refused listing read as 0 files matching."""
    claude = repo / "CLAUDE.md"
    claude.write_text(
        claude.read_text(encoding="utf-8").replace("- `LICENSE`\n", "- `LICENSE`\n- `hooks/*`\n"),
        encoding="utf-8",
    )
    hooks = repo / "hooks"
    hooks.mkdir()
    (hooks / "pre-commit").write_text("#!/bin/sh\n", encoding="utf-8")
    before, _skips = drift_guard.guard_frozen(repo)
    assert before["status"] == "PASS", before["detail"]
    assert any("hooks/* -> 1 file(s)" in line for line in before["detail"]), before["detail"]

    with refused(hooks):
        guard, skips = drift_guard.guard_frozen(repo)

    rendered = "\n".join(guard["detail"])
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert "hooks/* -> NOT LISTED" in rendered, rendered
    assert any(skip["path"] == "hooks" for skip in skips), skips


def _plant_roadmap_over_its_soft_budget(root: Path) -> None:
    doc_budget = drift_guard._load_doc_budget()  # noqa: SLF001 - the budget's own owner
    roadmap = root / ROADMAP_RELATIVE
    text = roadmap.read_text(encoding="utf-8")
    line = "Padding for the soft budget plant, carrying no item and no date.\n"
    repeats = doc_budget.ROADMAP_BUDGET // len(line) + 1
    roadmap.write_text(text + line * repeats, encoding="utf-8", newline="\n")
    assert roadmap.stat().st_size > doc_budget.ROADMAP_BUDGET, "the plant is under the budget"


def _plant_port_with_no_record(root: Path) -> None:
    ports = root / "config" / "ports.json"
    payload = json.loads(ports.read_text(encoding="utf-8"))
    payload["band"]["end"] = payload["band"]["end"] + 1
    ports.write_text(json.dumps(payload, indent=2), encoding="utf-8")


#: The allowlist, from the other side: every soft WARN that reads real input.
ADVISORY_PLANTS = {
    "a-soft-budget": ("a", _plant_roadmap_over_its_soft_budget),
    "e-port-with-no-record": ("e", _plant_port_with_no_record),
}


@pytest.mark.parametrize("plant", sorted(ADVISORY_PLANTS))
def test_an_advisory_warn_as_the_only_non_pass_guard_stays_clean(
    repo: Path, capsys: pytest.CaptureFixture[str], plant: str
) -> None:
    """The control in the other direction: a soft finding never turns into a failure.

    Asserted on the flag AND on both output paths, so a verdict that ignored
    the flag and passed every WARN would still redden the sweep above.
    """
    guard_id, apply = ADVISORY_PLANTS[plant]
    apply(repo)

    code, report = run_main(capsys)
    assert non_pass(report) == {guard_id: "WARN"}, report["guards"]
    assert (report["verdict"], code) == ("CLEAN", 0)
    assert report["ungraded"] == []
    assert guard_of(report, guard_id)["advisory"] is True

    text_code = drift_guard.main([])
    printed = capsys.readouterr().out.splitlines()
    verdicts = [line for line in printed if line.startswith("VERDICT:")]
    assert text_code == 0
    assert verdicts, printed
    assert verdicts[0].startswith("VERDICT: CLEAN with warnings"), verdicts


def test_an_advisory_flag_on_anything_but_a_warn_is_refused() -> None:
    """A PASS or a FAIL marked advisory is a contradiction, so it cannot be built."""
    for status in ("PASS", "FAIL"):
        with pytest.raises(ValueError, match="advisory"):
            drift_guard._guard("x", "a synthetic guard", status, [], advisory=True)  # noqa: SLF001


def test_the_real_tree_soft_warnings_still_exit_zero() -> None:
    """The control on the REAL tree, through the command CI runs.

    The real tree carries soft budget overshoots today. They must stay
    advisory: ``python tools/drift_guard.py`` exits 0 and ``--json`` reports
    CLEAN. Any WARN on the real tree is asserted advisory BY ITS FLAG - a
    could-not-look WARN here would be exactly the defect CS-1113 closed.
    DISCLOSED: if the real tree ever carries no WARN at all, this arm still
    grades the exit code but no longer grades a soft warning; the synthetic
    advisory arms above carry that half regardless.
    """
    command = [sys.executable, "-B", str(DRIFT_GUARD_SOURCE)]
    text = subprocess.run(
        command, capture_output=True, text=True, timeout=600, check=False, cwd=REPO_ROOT
    )
    as_json = subprocess.run(
        [*command, "--json"],
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
        cwd=REPO_ROOT,
    )
    report = json.loads(as_json.stdout)
    failed = [guard["id"] for guard in report["guards"] if guard["status"] == "FAIL"]
    unread = [
        guard["id"]
        for guard in report["guards"]
        if guard["status"] == "WARN" and guard.get("advisory") is not True
    ]
    assert failed == [], f"the real tree carries DRIFT in {failed}, so this control grades nothing"
    assert unread == [], f"the real tree carries could-not-look WARNs in {unread}"
    assert (report["verdict"], as_json.returncode) == ("CLEAN", 0)
    assert text.returncode == 0, "python tools/drift_guard.py exited non-zero on the real tree"


# ---------------------------------------------------------------------------
# CS-1117 - four could-not-look residuals CS-1115 left behind
#
# Guard (c) skipped a file it could not read and still said PASS. Guard (b)
# skipped an unreadable leaf and still said PASS while its citation count
# quietly shrank. Guard (a) measured a DIRECTORY carrying a budgeted name as a
# 0 byte file inside budget. Guard (b) called an indexed directory-named leaf
# "does not exist". Every read fault below is REAL - `refused` - and every arm
# carries a control that the unfaulted tree is graded exactly as before.
# ---------------------------------------------------------------------------


def _detail(guard: dict[str, Any]) -> str:
    return "\n".join(guard["detail"])


def _charset_tree(root: Path) -> list[Path]:
    """Two authored text files, both clean, and nothing else."""
    root.mkdir(parents=True, exist_ok=True)
    first = root / "a-note.md"
    first.write_text("# clean\n", encoding="utf-8")
    second = root / "b_module.py"
    second.write_text("VALUE = 1\n", encoding="utf-8")
    return [first, second]


def test_an_unreadable_file_is_a_charset_warn_naming_it_never_a_silent_skip(
    tmp_path: Path,
) -> None:
    """The CS-1117 acceptance arm for guard (c): WARN, not advisory, the file named."""
    files = _charset_tree(tmp_path)
    before, _skips = drift_guard.guard_charset(tmp_path, files, "test enumeration")
    assert before["status"] == "PASS", _detail(before)
    assert "text files checked: 2" in before["detail"], _detail(before)

    with refused(files[1]):
        assert files[1].is_file(), "control: the refused file no longer stats as a file"
        with pytest.raises(PermissionError):
            files[1].read_bytes()
        guard, skips = drift_guard.guard_charset(tmp_path, files, "test enumeration")

    rendered = _detail(guard)
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert "b_module.py NOT READ" in rendered, rendered
    assert "text files checked: 1" in guard["detail"], rendered
    assert "text files listed: 2" in guard["detail"], rendered
    assert any(skip["path"] == "b_module.py" for skip in skips), skips


def test_an_unreadable_file_does_not_hide_a_charset_violation_that_was_read(
    tmp_path: Path,
) -> None:
    """The fault narrows what is graded; it never pardons a byte that WAS read."""
    files = _charset_tree(tmp_path)
    files[0].write_bytes(b"# not clean \xe2\x80\x94\n")

    with refused(files[1]):
        guard, _skips = drift_guard.guard_charset(tmp_path, files, "test enumeration")

    rendered = _detail(guard)
    assert guard["status"] == "FAIL", rendered
    assert "a-note.md -> line 1" in rendered, rendered
    assert "b_module.py NOT READ" in rendered, rendered


def test_a_file_gone_before_the_charset_read_is_absent_not_unreadable(tmp_path: Path) -> None:
    """The anti-narrowing control: a file that is not there is not an unread file."""
    files = _charset_tree(tmp_path)
    files[1].unlink()

    guard, skips = drift_guard.guard_charset(tmp_path, files, "test enumeration")

    rendered = _detail(guard)
    assert guard["status"] == "PASS", rendered
    assert "NOT READ" not in rendered, rendered
    reasons = [skip["reason"] for skip in skips if skip["path"] == "b_module.py"]
    assert len(reasons) == 1, skips
    assert reasons[0].startswith("absent"), reasons


def test_an_unreadable_tracked_file_makes_the_run_ungraded(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Through main() on both output paths: one unread .py file is never CLEAN.

    Guard (k) reads the same text population for a second statement of the
    lane's target, so it is the second could-not-look WARN (its CS-1117
    sibling); no other guard reads a module under tools/.
    """
    planted = repo / "tools" / "zz_cs1117_plant.py"
    planted.parent.mkdir(parents=True, exist_ok=True)
    planted.write_text("VALUE = 1\n", encoding="utf-8")
    code, report = run_main(capsys)
    assert (report["verdict"], code) == ("CLEAN", 0), "control: the planted tree is not clean"

    with refused(planted):
        code, report = run_main(capsys)
        text_code = drift_guard.main([])
        printed = capsys.readouterr().out.splitlines()

    assert non_pass(report) == {"c": "WARN", "k": "WARN"}, report["guards"]
    assert report["verdict"] == "UNGRADED"
    assert code != 0
    assert sorted(report["ungraded"]) == ["c", "k"]
    assert text_code != 0, "the text path exited 0 over an unread file"
    verdicts = [line for line in printed if line.startswith("VERDICT:")]
    assert verdicts, printed
    assert verdicts[0].startswith("VERDICT: UNGRADED"), verdicts


def test_the_real_tree_charset_population_is_every_listed_text_file() -> None:
    """The anti-narrowing control on the REAL tree: checked equals listed, nothing unread.

    The unread partition is new, so the one thing it must never do on a healthy
    tree is move a file out of the checked count.
    """
    files, source, _skips = drift_guard.enumerate_files(REPO_ROOT)
    text = [path for path in files if drift_guard._classify(path)[0]]  # noqa: SLF001
    guard, _guard_skips = drift_guard.guard_charset(REPO_ROOT, files, source)

    rendered = _detail(guard)
    assert len(text) > 1, "the real tree lists no text file, so this control grades nothing"
    assert f"text files checked: {len(text)}" in guard["detail"], rendered
    assert f"text files listed: {len(text)}" in guard["detail"], rendered
    assert "NOT READ" not in rendered, rendered


def _ordinary_leaves(memory: Path) -> list[Path]:
    """Every leaf that is not MEMORY.md or an INDEX_*.md routing file, sorted."""
    return [
        path
        for path in sorted(memory.glob("*.md"))
        if path.name != "MEMORY.md" and not path.name.lower().startswith("index_")
    ]


def _cited_leaf(memory: Path, avoid: Path | None = None) -> tuple[Path, int]:
    """The first ordinary leaf carrying a citation, and how many it carries."""
    for path in _ordinary_leaves(memory):
        if path == avoid:
            continue
        excluded = {(k, t) for name, k, t in KNOWN_IN_CODE_TOKENS if name == path.name}
        count = len(raw_citations(path) - excluded)
        if count:
            return path, count
    message = "no ordinary leaf carries a citation"
    raise AssertionError(message)


def test_an_unreadable_memory_leaf_is_a_warn_and_the_population_says_so(tmp_path: Path) -> None:
    """The CS-1117 acceptance arm for guard (b): WARN, and the count names what it covers.

    MEASURED before the fix on the real store: 62 of 62 fell to 60 of 60 and
    the guard still said PASS.
    """
    root = memory_copy(tmp_path)
    memory = root / "memory"
    ordinary = _ordinary_leaves(memory)
    index_expected, leaf_expected = expected_citation_counts(memory)
    leaf, carried = _cited_leaf(memory)
    status, rendered = memory_verdict(root)
    assert status == "PASS", rendered
    assert reported_citation_counts(rendered) == (index_expected, leaf_expected), rendered

    with refused(leaf):
        assert leaf.is_file(), "control: the refused leaf no longer stats as a file"
        with pytest.raises(PermissionError):
            leaf.read_bytes()
        guard, skips = drift_guard.guard_memory(root)

    rendered = _detail(guard)
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert f"memory/{leaf.name} NOT READ" in rendered, rendered
    assert reported_citation_counts(rendered) == (index_expected, leaf_expected - carried)
    assert f"in {len(ordinary) - 1} of {len(ordinary)} listed leaves" in rendered, rendered
    assert any(skip["path"] == leaf.name for skip in skips), skips


def test_the_real_memory_population_states_every_listed_leaf_as_read(tmp_path: Path) -> None:
    """The anti-narrowing control: an unfaulted store reads every leaf it lists."""
    root = memory_copy(tmp_path)
    memory = root / "memory"
    ordinary = _ordinary_leaves(memory)
    routing = [path for path in memory.glob("*.md") if path not in ordinary]

    status, rendered = memory_verdict(root)

    assert status == "PASS", rendered
    assert f"in {len(ordinary)} of {len(ordinary)} listed leaves" in rendered, rendered
    assert f"in {len(routing)} of {len(routing)} listed routing files" in rendered, rendered
    assert reported_citation_counts(rendered) == expected_citation_counts(memory)
    assert "NOT READ" not in rendered, rendered


def test_an_unreadable_memory_leaf_does_not_hide_a_dangling_citation_elsewhere(
    tmp_path: Path,
) -> None:
    """A FAIL on a leaf that was read still wins, and the unread leaf is still named."""
    root = memory_copy(tmp_path)
    memory = root / "memory"
    assert not (memory / f"{GHOST_LEAF}.md").exists(), "the plant names a real file"
    planted = plant(root, f"\nThe lesson is owned by [[{GHOST_LEAF}]].\n")
    leaf, _carried = _cited_leaf(memory, avoid=planted)

    with refused(leaf):
        status, rendered = memory_verdict(root)

    assert status == "FAIL", rendered
    assert f"[[{GHOST_LEAF}]], which does not exist" in rendered, rendered
    assert f"memory/{leaf.name} NOT READ" in rendered, rendered


def test_an_unreadable_memory_leaf_makes_the_run_ungraded(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Through main(): every guard that reads the leaf WARNs, and none is advisory.

    Guard (a) only stats the leaf, and a stat still answers under the fault, so
    it stays PASS; (c), (g) and (k) read it and are its siblings.
    """
    memory = repo / "memory"
    leaf = memory / "a-leaf.md"
    leaf.write_text("# A leaf\n\nSee [the index](MEMORY.md).\n", encoding="utf-8")
    index = memory / "MEMORY.md"
    index.write_text(index.read_text(encoding="utf-8") + "- [A leaf](a-leaf.md)\n", "utf-8")
    code, report = run_main(capsys)
    assert (report["verdict"], code) == ("CLEAN", 0), "control: the leaf tree is not clean"

    with refused(leaf):
        code, report = run_main(capsys)

    assert non_pass(report) == dict.fromkeys(["b", "c", "g", "k"], "WARN"), report["guards"]
    assert report["verdict"] == "UNGRADED"
    assert code != 0
    for each in ("b", "c", "g", "k"):
        assert guard_of(report, each)["advisory"] is False, each


@pytest.mark.parametrize(
    ("citation", "quoted"),
    [
        ("- [Z](zz-cs1117-dir.md)\n", "](zz-cs1117-dir.md)"),
        ("- [[zz-cs1117-dir]]\n", "[[zz-cs1117-dir]]"),
    ],
)
def test_an_indexed_directory_carrying_a_leaf_name_is_named_as_a_directory(
    repo: Path, citation: str, quoted: str
) -> None:
    """Guard (b) names the defect that is there: a directory, never a missing file.

    The control beside it is a genuinely absent target, which must still read
    "does not exist" - so the new wording cannot swallow the old finding.
    """
    memory = repo / "memory"
    (memory / "zz-cs1117-dir.md").mkdir()
    index = memory / "MEMORY.md"
    ghost = f"{GHOST_LEAF}.md"
    assert not (memory / ghost).exists(), "the control names a real file"
    index.write_text(
        index.read_text(encoding="utf-8") + citation + f"- [G]({ghost})\n", encoding="utf-8"
    )

    guard, _skips = drift_guard.guard_memory(repo)

    rendered = _detail(guard)
    assert guard["status"] == "FAIL", rendered
    assert f"cites {quoted}, which is a directory, not a file" in rendered, rendered
    assert "memory/zz-cs1117-dir.md is a directory, not a leaf" in rendered, rendered
    assert f"cites ]({ghost}), which does not exist" in rendered, rendered
    assert "zz-cs1117-dir]], which does not exist" not in rendered, rendered
    assert "zz-cs1117-dir.md), which does not exist" not in rendered, rendered
    assert "NOT READ" not in rendered, rendered


def test_a_directory_carrying_a_budgeted_name_fails_guard_a(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Guard (a) measured a directory as a 0 byte file inside budget and said PASS."""
    swap_for_directory(repo / UPSTREAM_WATCH_RELATIVE)

    guard, _skips = drift_guard.guard_budgets(repo)
    rendered = _detail(guard)
    assert guard["status"] == "FAIL", rendered
    assert f"NOT A FILE {UPSTREAM_WATCH_RELATIVE}" in rendered, rendered

    code, report = run_main(capsys)
    assert non_pass(report) == {"a": "FAIL"}, report["guards"]
    assert (report["verdict"], code != 0) == ("DRIFT", True)


def test_an_unreadable_markdown_file_is_a_dated_guard_warn(tmp_path: Path) -> None:
    """The guard (g) sibling of the charset residual - an unread file was a bare skip."""
    files = _charset_tree(tmp_path)
    before, _skips = drift_guard.guard_dated(tmp_path, files)
    assert before["status"] == "PASS", _detail(before)

    with refused(files[0]):
        guard, skips = drift_guard.guard_dated(tmp_path, files)

    rendered = _detail(guard)
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert "a-note.md NOT READ" in rendered, rendered
    assert any(skip["path"] == "a-note.md" for skip in skips), skips


def test_an_unreadable_file_is_a_tier1_guard_warn(repo: Path) -> None:
    """The guard (k) sibling: its second-owner scan skipped an unread file and passed."""
    files = _charset_tree(repo / "zz-cs1117")
    everything, _source, _skips = drift_guard.enumerate_files(repo)
    before, _before_skips = drift_guard.guard_tier1_budget(repo, everything)
    assert before["status"] == "PASS", _detail(before)

    with refused(files[1]):
        guard, skips = drift_guard.guard_tier1_budget(repo, everything)

    rendered = _detail(guard)
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert "zz-cs1117/b_module.py NOT READ" in rendered, rendered
    assert any(skip["path"] == "zz-cs1117/b_module.py" for skip in skips), skips


# ---------------------------------------------------------------------------
# CS-1120 - the residues CS-1117 left: a listed LINK whose target is gone, a
# directory the walk could not list, and a memory routing file that could not
# be read. Each was a could-not-look that read as absent, as nothing, or as a
# different defect. Every fault below is REAL - a link on disk, an exclusive
# handle or a mode of zero - never a stub.
# ---------------------------------------------------------------------------


def dangling_link(path: Path) -> str:
    """Replace ``path`` with a REAL link whose target does not exist.

    A symbolic link where this account may create one - MEASURED to work on the
    Windows development account and on POSIX. Where Windows refuses it, a
    directory junction to a removed directory is the same fault to an lstat:
    present, while a stat and a read say nothing is there. SKIPPED only where
    neither can be made, and the reason says so.

    Args:
        path: The file to replace. It need not exist.

    Returns:
        ``"symlink"`` or ``"junction"``, whichever was made.
    """
    path.unlink(missing_ok=True)
    target = path.with_name(f"{path.name}-cs1120-gone")
    kind = "symlink"
    try:
        path.symlink_to(target)
    except OSError as refused_link:
        if sys.platform != "win32":
            pytest.skip(f"this account cannot create a symbolic link: {refused_link.strerror}")
        import _winapi  # noqa: PLC0415 - Windows-only

        target.mkdir()
        try:
            _winapi.CreateJunction(str(target), str(path))
        except OSError as refused_junction:
            target.rmdir()
            pytest.skip(
                "this account can create neither a symbolic link nor a junction: "
                f"{refused_link.strerror}; {refused_junction.strerror}"
            )
        target.rmdir()
        kind = "junction"
    path.lstat()
    assert not path.exists(), "control: the link is not dangling"
    assert not target.exists(), "control: the link target still exists"
    return kind


def _assert_not_absent(skips: list[Any], relative: str, kind: str) -> None:
    """The link's skip is recorded once, and never under the absent label."""
    reasons = [skip["reason"] for skip in skips if skip["path"] == relative]
    assert len(reasons) == 1, skips
    assert not reasons[0].startswith(drift_guard.ABSENT_WHEN_READ), reasons
    if kind == "symlink":
        assert reasons[0].startswith(drift_guard.DANGLING_WHEN_READ), reasons


def test_a_dangling_link_is_a_charset_warn_never_absent(tmp_path: Path) -> None:
    """CS-1120 (a) for guard (c): the listed link is NOT READ, and listed stays 2."""
    files = _charset_tree(tmp_path)
    kind = dangling_link(files[1])

    guard, skips = drift_guard.guard_charset(tmp_path, files, "test enumeration")

    rendered = _detail(guard)
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert "b_module.py NOT READ" in rendered, rendered
    assert "text files checked: 1" in guard["detail"], rendered
    assert "text files listed: 2" in guard["detail"], rendered
    _assert_not_absent(skips, "b_module.py", kind)


def test_a_dangling_link_is_a_dated_guard_warn_never_absent(tmp_path: Path) -> None:
    """CS-1120 (a), the guard (g) sibling of the charset site."""
    files = _charset_tree(tmp_path)
    kind = dangling_link(files[0])

    guard, skips = drift_guard.guard_dated(tmp_path, files)

    rendered = _detail(guard)
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert "a-note.md NOT READ" in rendered, rendered
    _assert_not_absent(skips, "a-note.md", kind)


def test_a_dangling_link_is_a_tier1_guard_warn_never_absent(repo: Path) -> None:
    """CS-1120 (a), the guard (k) sibling of the charset site."""
    files = _charset_tree(repo / "zz-cs1120")
    kind = dangling_link(files[1])
    everything, _source, _skips = drift_guard.enumerate_files(repo)

    guard, skips = drift_guard.guard_tier1_budget(repo, everything)

    rendered = _detail(guard)
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert "zz-cs1120/b_module.py NOT READ" in rendered, rendered
    _assert_not_absent(skips, "zz-cs1120/b_module.py", kind)


def test_a_dangling_link_makes_the_run_ungraded(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Through main(): the link is read by (c), (g) and (k), and none is CLEAN or advisory."""
    link = repo / "zz-cs1120-link.md"
    link.write_text("# clean\n", encoding="utf-8")
    code, report = run_main(capsys)
    assert (report["verdict"], code) == ("CLEAN", 0), "control: the planted tree is not clean"

    dangling_link(link)
    code, report = run_main(capsys)

    readers = ["c", "g", "k"]
    assert non_pass(report) == dict.fromkeys(readers, "WARN"), report["guards"]
    assert (report["verdict"], code != 0) == ("UNGRADED", True)
    for each in readers:
        assert guard_of(report, each)["advisory"] is False, each


def _tracked_tree(root: Path, monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    """The charset tree, staged in a REAL throwaway index so enumeration takes the git path."""
    from tests import conftest  # noqa: PLC0415 - the one git runner the suite owns
    from tests.git_env import relocates  # noqa: PLC0415

    for name in [key for key in os.environ if relocates(key)]:
        monkeypatch.delenv(name)
    files = _charset_tree(root)
    for args in (("init", "--quiet"), ("add", "--", "a-note.md", "b_module.py")):
        proc = conftest.run_git(root, *args)
        if proc is None:
            pytest.skip("git is not installed, so no index can be built")
        assert proc.returncode == 0, f"control: git {args[0]} exited {proc.returncode}"
    return files


def test_a_tracked_dangling_link_is_listed_and_read_never_dropped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS-1120 (a) at enumeration: an index entry an lstat finds is handed to the readers.

    It was skipped as "in the git index but not on disk", so the charset guard
    never saw it: listed fell from 2 to 1 and the verdict was PASS.
    """
    files = _tracked_tree(tmp_path, monkeypatch)
    kind = dangling_link(files[1])

    listed, source, _skips = drift_guard.enumerate_files(tmp_path)
    guard, skips = drift_guard.guard_charset(tmp_path, listed, source)

    rendered = _detail(guard)
    assert source.startswith("git ls-files"), source
    assert files[1] in listed, listed
    assert guard["status"] == "WARN", rendered
    assert "b_module.py NOT READ" in rendered, rendered
    assert "text files listed: 2" in guard["detail"], rendered
    _assert_not_absent(skips, "b_module.py", kind)


def test_a_tracked_file_that_is_really_gone_is_still_only_a_skip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The anti-narrowing control: nothing on disk is not a could-not-look."""
    files = _tracked_tree(tmp_path, monkeypatch)
    files[1].unlink()

    listed, source, skips = drift_guard.enumerate_files(tmp_path)
    guard, _guard_skips = drift_guard.guard_charset(tmp_path, listed, source)

    rendered = _detail(guard)
    assert source.startswith("git ls-files"), source
    assert files[1] not in listed, listed
    assert guard["status"] == "PASS", rendered
    assert "NOT READ" not in rendered, rendered
    assert {"path": "b_module.py", "reason": "in the git index but not on disk"} in skips


def _walk_tree(root: Path) -> Path:
    """A clean top-level file and a subdirectory holding a markdown and a module."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    below = root / "zz-cs1120-dir"
    below.mkdir()
    (below / "a-note.md").write_text("# clean\n", encoding="utf-8")
    (below / "b_module.py").write_text("VALUE = 1\n", encoding="utf-8")
    return below


def test_an_unlistable_directory_in_the_walk_is_a_charset_warn(tmp_path: Path) -> None:
    """CS-1120 (c): the walk recorded a skip and the guard said PASS over files never listed."""
    root = tmp_path / "walked"
    below = _walk_tree(root)
    files, source, _skips = drift_guard.enumerate_files(root)
    before, _before_skips = drift_guard.guard_charset(root, files, source)
    assert source.startswith("directory walk"), source
    assert before["status"] == "PASS", _detail(before)
    assert "text files listed: 3" in before["detail"], _detail(before)

    with refused(below):
        with pytest.raises(PermissionError):
            list(below.iterdir())
        files, source, _skips = drift_guard.enumerate_files(root)
        guard, _guard_skips = drift_guard.guard_charset(root, files, source)

    rendered = _detail(guard)
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert "zz-cs1120-dir/ NOT LISTED" in rendered, rendered
    assert "text files listed: 1" in guard["detail"], rendered


def test_an_unlistable_directory_makes_the_run_ungraded(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Through main(): (c), (g) and (k) each read the walked population, so each says so.

    MEASURED before the fix: guard (a) alone was UNGRADED here, because
    doc_budget walks the root for nested budgeted files and names what it could
    not list. The three guards that read every listed file said PASS.
    """
    below = _walk_tree(repo)
    code, report = run_main(capsys)
    assert (report["verdict"], code) == ("CLEAN", 0), "control: the planted tree is not clean"

    with refused(below):
        code, report = run_main(capsys)

    readers = ["c", "g", "k"]
    assert non_pass(report) == dict.fromkeys(["a", *readers], "WARN"), report["guards"]
    assert (report["verdict"], code != 0) == ("UNGRADED", True)
    for each in readers:
        assert guard_of(report, each)["advisory"] is False, each
        assert "zz-cs1120-dir/ NOT LISTED" in _detail(guard_of(report, each)), each


def test_an_unreadable_memory_index_is_a_warn_never_unreachable_leaves(tmp_path: Path) -> None:
    """CS-1120 (c): a refused MEMORY.md read as every leaf UNREACHABLE - a FAIL naming drift.

    Nothing was unreachable; the routing table was never read. That is
    could-not-look, and reachability is ungraded rather than failed.
    """
    root = memory_copy(tmp_path)
    index = root / "memory" / "MEMORY.md"
    status, rendered = memory_verdict(root)
    assert status == "PASS", rendered

    with refused(index):
        assert index.is_file(), "control: the refused index no longer stats as a file"
        guard, _skips = drift_guard.guard_memory(root)

    rendered = _detail(guard)
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert "UNREACHABLE" not in rendered, rendered
    assert "memory/MEMORY.md NOT READ" in rendered, rendered
    assert "reachability NOT GRADED" in rendered, rendered


def test_an_unreadable_routing_child_is_a_warn_never_unreachable_leaves(tmp_path: Path) -> None:
    """The INDEX_*.md sibling: a refused child hid the leaves only it routes to."""
    root = memory_copy(tmp_path)
    memory = root / "memory"
    child = memory / "INDEX_zz_cs1120.md"
    leaf = memory / "zz-cs1120-routed-leaf.md"
    assert not child.exists(), "the plant names a real routing file"
    assert not leaf.exists(), "the plant names a real leaf"
    leaf.write_text("# Routed\n\nSee [the index](MEMORY.md).\n", encoding="utf-8", newline="\n")
    child.write_text("# Child\n\n- [Routed](zz-cs1120-routed-leaf.md)\n", "utf-8", newline="\n")
    index = memory / "MEMORY.md"
    index.write_text(
        index.read_text(encoding="utf-8") + "- [Child](INDEX_zz_cs1120.md)\n", "utf-8", newline="\n"
    )
    status, rendered = memory_verdict(root)
    assert status == "PASS", rendered

    with refused(child):
        guard, _skips = drift_guard.guard_memory(root)

    rendered = _detail(guard)
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert "UNREACHABLE" not in rendered, rendered
    assert "memory/INDEX_zz_cs1120.md NOT READ" in rendered, rendered


#: The routing child the case arms plant, spelled the way a real one is.
IDXCASE_CHILD = "INDEX_zz_idxcase.md"
#: The same name as the walk's lowercased token spells it.
IDXCASE_LOWERED = IDXCASE_CHILD.lower()


def _plant_routed_child(tmp_path: Path) -> tuple[Path, Path]:
    """A copied store whose MEMORY.md routes to a child that alone routes to a leaf.

    Returns:
        ``(fake repository root, the memory directory)``.
    """
    root = memory_copy(tmp_path)
    memory = root / "memory"
    child = memory / IDXCASE_CHILD
    leaf = memory / "zz-idxcase-routed-leaf.md"
    assert not child.exists(), "the plant names a real routing file"
    assert not leaf.exists(), "the plant names a real leaf"
    leaf.write_text("# Routed\n\nSee [the index](MEMORY.md).\n", encoding="utf-8", newline="\n")
    child.write_text(
        "# Child\n\n- [Routed](zz-idxcase-routed-leaf.md)\n", encoding="utf-8", newline="\n"
    )
    index = memory / "MEMORY.md"
    index.write_text(
        index.read_text(encoding="utf-8") + f"- [Child]({IDXCASE_CHILD})\n",
        encoding="utf-8",
        newline="\n",
    )
    return root, memory


def _case_sensitive_lookups(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``Path.is_file`` answer the way a case-sensitive filesystem does.

    CI's ubuntu leg failed the CS-1120 routing-child arm while Windows passed
    it: the walk built ``memory / "index_zz_cs1120.md"`` from a lowercased
    token and asked ``is_file()``, which a case-insensitive filesystem answers
    yes and ext4 answers no. A path is a file here only when its final
    component is spelled exactly as the directory lists it, so the Linux
    behaviour reproduces on this machine. Only the name is compared, never a
    parent, because a temporary root can carry a short 8.3 spelling.
    """
    real_is_file = Path.is_file

    def is_file(self: Path, *args: Any, **kwargs: Any) -> bool:
        try:
            # os.listdir, not Path.iterdir: arms patch iterdir, never this.
            spelled = self.name in os.listdir(self.parent)  # noqa: PTH208
        except OSError:
            spelled = False
        return spelled and real_is_file(self, *args, **kwargs)

    monkeypatch.setattr(Path, "is_file", is_file)


def test_the_case_sensitive_emulation_refuses_the_lowered_spelling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Control: the emulation really answers no to the lowered name, yes to the real one."""
    _root, memory = _plant_routed_child(tmp_path)
    _case_sensitive_lookups(monkeypatch)

    assert (memory / IDXCASE_CHILD).is_file(), "the real spelling must still be a file"
    assert not (memory / IDXCASE_LOWERED).is_file(), "the emulation did not bind"


def test_a_routing_child_is_followed_where_names_are_case_sensitive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The ubuntu red, reproduced on any OS: an INDEX_ child's leaves stay reachable."""
    root, _memory = _plant_routed_child(tmp_path)
    _case_sensitive_lookups(monkeypatch)

    status, rendered = memory_verdict(root)

    assert "UNREACHABLE" not in rendered, rendered
    assert status == "PASS", rendered


def test_the_walk_reaches_a_childs_leaf_where_names_are_case_sensitive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The shared walk itself, as `tools/memory_sync.py` consumes it."""
    _root, memory = _plant_routed_child(tmp_path)
    _case_sensitive_lookups(monkeypatch)

    reachable = drift_guard.reachable_from_index(memory, memory / "MEMORY.md")

    assert "zz-idxcase-routed-leaf" in reachable, sorted(reachable)


def test_two_routing_files_differing_only_by_case_are_a_finding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A token two entries answer is ambiguous - named, never resolved to one silently.

    On a case-sensitive filesystem the twin is written for real. Where the
    filesystem cannot hold both spellings, the directory listing is made to
    carry the twin, which then reads as the same file.
    """
    root, memory = _plant_routed_child(tmp_path)
    twin = memory / IDXCASE_LOWERED
    if not twin.exists():
        twin.write_text(
            "# Twin\n\n- [Routed](zz-idxcase-routed-leaf.md)\n", encoding="utf-8", newline="\n"
        )
    else:
        real_iterdir = Path.iterdir

        def iterdir(self: Path) -> Iterator[Path]:
            listed = list(real_iterdir(self))
            if self == memory:
                listed.append(twin)
            return iter(listed)

        monkeypatch.setattr(Path, "iterdir", iterdir)
    names = {path.name for path in memory.iterdir()}
    assert {IDXCASE_CHILD, IDXCASE_LOWERED} <= names, "control: the twin is not listed"

    status, rendered = memory_verdict(root)

    assert status == "FAIL", rendered
    assert "DIFFER ONLY BY CASE" in rendered, rendered
    assert f"memory/{IDXCASE_CHILD}" in rendered, rendered
    assert f"memory/{IDXCASE_LOWERED}" in rendered, rendered
    assert "UNREACHABLE" not in rendered, rendered


def test_a_memory_listing_the_walk_is_refused_is_a_warn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The walk lists the directory to find a child; a refused listing grades no leaf."""
    root, memory = _plant_routed_child(tmp_path)
    real_iterdir = Path.iterdir
    listings: list[Path] = []

    def iterdir(self: Path) -> Iterator[Path]:
        if self == memory:
            listings.append(self)
            if len(listings) > 1:
                raise PermissionError(errno.EACCES, "refused listing")
        return real_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", iterdir)

    guard, skips = drift_guard.guard_memory(root)

    rendered = _detail(guard)
    assert len(listings) > 1, "control: the walk never listed the directory"
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert "UNREACHABLE" not in rendered, rendered
    assert "reachability NOT GRADED" in rendered, rendered
    assert any("not listed" in skip["reason"] for skip in skips), skips


def test_a_leaf_nothing_routes_to_is_still_unreachable_beside_a_read_index(
    tmp_path: Path,
) -> None:
    """The anti-narrowing control: a readable index still FAILS an unrouted leaf."""
    root = memory_copy(tmp_path)
    orphan = root / "memory" / "zz-cs1120-orphan.md"
    orphan.write_text("# Orphan\n", encoding="utf-8", newline="\n")

    status, rendered = memory_verdict(root)

    assert status == "FAIL", rendered
    assert "UNREACHABLE" in rendered, rendered
    assert "memory/zz-cs1120-orphan.md" in rendered, rendered
    assert "NOT GRADED" not in rendered, rendered


#: CS-1120 (b) - what reading a directory raises, MEASURED: ``IsADirectoryError``
#: on POSIX, and ``PermissionError`` (errno 13) on Windows.
DIRECTORY_READ_ERROR = PermissionError if os.name == "nt" else IsADirectoryError


def test_a_directory_in_roadmaps_place_is_a_guard_j_could_not_look_warn(repo: Path) -> None:
    """CS-1120 (b): guard (j)'s directory read path, graded at the guard.

    CS-1117 moved the driver-level arm to an exclusive handle, because a
    directory under the name is guard (a)'s NOT A FILE FAIL. That left guard
    (j)'s read of a directory unexercised on POSIX, so it is graded here, where
    guard (a) is not in the frame.
    """
    roadmap = repo / ROADMAP_RELATIVE
    swap_for_directory(roadmap)
    with pytest.raises(DIRECTORY_READ_ERROR):
        roadmap.read_text(encoding="utf-8")

    guard, skips = drift_guard.guard_index(repo)

    rendered = _detail(guard)
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert f"{ROADMAP_RELATIVE} NOT READ" in rendered, rendered
    assert any(skip["path"] == ROADMAP_RELATIVE for skip in skips), skips


# --- CS-1153: the walk prunes by its own rule ------------------------------
#
# WHY THESE DRIVE _walk DIRECTLY RATHER THAN enumerate_files. The pruning under
# test was, before CS-1153, done by the ENUMERATION STRATEGY and not by the
# walk: enumerate_files() prefers the git index, which never lists an ignored
# path, and falls back to _walk only on an empty index - which on a populated
# repository never happens. So every arm below calls _walk itself. A test
# routed through enumerate_files would be green on the defect, because it would
# never reach the walk at all.
#
# WHY THE ASSERTION IS A SET EQUALITY. "the pruned root is absent" passes for
# the correct walk AND for a walk that collapsed and returned nothing. The
# equality pins both halves at once: exactly the authored files, and nothing
# from any pruned subtree.


def _cs1153_tree(root: Path) -> None:
    """A repository-shaped tree carrying one file inside every pruned root.

    Each planted file has a DISTINCT name, so a set equality naming only the
    authored three fails by naming the intruder rather than by a bare count.
    """
    (root / "docs").mkdir(parents=True)
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    (root / "docs" / "deep.md").write_text("# clean\n", encoding="utf-8")

    # Authored, tracked, and INSIDE .claude - so a rule that pruned the whole
    # of .claude rather than .claude/worktrees fails this arm.
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")

    # A populated worktrees directory: one child carrying the .git marker a
    # linked worktree really carries, and one child carrying none. Pruning the
    # CONTAINER is what covers the second; the marker alone would not.
    marked = root / ".claude" / "worktrees" / "slice-marked"
    marked.mkdir(parents=True)
    (marked / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    (marked / "worktree_marked.md").write_text("# copy\n", encoding="utf-8")
    unmarked = root / ".claude" / "worktrees" / "slice-unmarked"
    unmarked.mkdir(parents=True)
    (unmarked / "worktree_unmarked.md").write_text("# copy\n", encoding="utf-8")

    for name in ("work", "certs", "corpus", "moon_sync_inbox", "data"):
        (root / name).mkdir()
        (root / name / f"{name}_leaf.md").write_text("# local\n", encoding="utf-8")


_ASK_GIT: Final = object()


def _walked(
    root: Path,
    worktrees: tuple[str, ...] = (),
    ignored: object = None,
) -> set[str]:
    """The walk's files as root-relative posix strings.

    ``worktrees`` defaults to EMPTY and ``ignored`` to NONE so no arm here
    spawns git against a tmp_path that is not a checkout: every arm states the
    authority it wants, and the default is the weakest one - git unreachable,
    the static floor alone deciding. Pass ``_ASK_GIT`` to let the walk ask git
    for itself, and an explicit ``frozenset()`` for the third state, which an
    adjudicator found load-bearing: git ANSWERING that nothing here is ignored.
    """
    kwargs = {} if ignored is _ASK_GIT else {"ignored": ignored}
    files, _skips = drift_guard._walk(root, worktrees=worktrees, **kwargs)  # noqa: SLF001
    return {path.relative_to(root).as_posix() for path in files}


def test_the_walk_prunes_the_gitignored_roots_by_its_own_rule(tmp_path: Path) -> None:
    """CS-1153: _walk, called directly, enters neither .claude/worktrees/ nor work/."""
    root = tmp_path / "tree"
    root.mkdir()
    _cs1153_tree(root)

    assert _walked(root) == {"top.md", "docs/deep.md", ".claude/settings.json"}


def test_the_walk_records_every_root_it_pruned(tmp_path: Path) -> None:
    """CS-1153: pruning is REPORTED, so a reader sees what was left out."""
    root = tmp_path / "tree"
    root.mkdir()
    _cs1153_tree(root)

    _files, skips = drift_guard._walk(root, worktrees=())  # noqa: SLF001
    pruned = {skip["path"] for skip in skips}
    assert pruned >= {
        ".claude/worktrees/",
        "work/",
        "certs/",
        "corpus/",
        "moon_sync_inbox/",
        "data/",
    }, skips
    assert all(skip["reason"] for skip in skips), skips


def test_the_walk_stops_at_a_checkout_root_at_an_unlisted_path(tmp_path: Path) -> None:
    """CS-1153: the .git marker prunes a checkout no name-based rule covers.

    The harness may put its worktrees anywhere. A directory carrying a .git
    entry is a checkout of its own and its files belong to THAT tree.
    """
    root = tmp_path / "tree"
    (root / "somewhere" / "nested-clone").mkdir(parents=True)
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    nested = root / "somewhere" / "nested-clone"
    (nested / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    (nested / "other_tree.md").write_text("# not ours\n", encoding="utf-8")

    assert _walked(root) == {"top.md"}


def test_the_walk_stops_at_a_registered_worktree_whose_marker_is_gone(
    tmp_path: Path,
) -> None:
    """CS-1153: `git worktree remove` deletes the marker BEFORE the files.

    In that window the marker test says nothing and the registration still
    does, so the registration is the test that holds through a teardown.
    """
    root = tmp_path / "tree"
    (root / "elsewhere" / "torn-down").mkdir(parents=True)
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    teardown = root / "elsewhere" / "torn-down"
    (teardown / "half_removed.md").write_text("# mid-teardown\n", encoding="utf-8")

    # The control: with no registration, the walk DOES enter it. Without this
    # arm the arm below passes on a walk that prunes "elsewhere" for some
    # unrelated reason, and the registration would never be exercised.
    assert _walked(root) == {"top.md", "elsewhere/torn-down/half_removed.md"}

    registered = (str(teardown.resolve()).lower(),)
    assert _walked(root, worktrees=registered) == {"top.md"}


#: CS-1153 - the floor on WALK_SKIP_ROOT_PATHS, one below the membership the set
#: shipped with. Named rather than written at the assertion so a future author
#: moving it has to move a constant with a reason attached.
_PRUNED_PATH_FLOOR = 18


def test_a_registered_worktree_is_named_as_one_even_carrying_its_marker(
    tmp_path: Path,
) -> None:
    """CS-1153: the branch ORDER is graded, not left to a silent mutant.

    A registered worktree that still carries its marker satisfies BOTH tests.
    Swapping the two branches keeps every file-level assertion green and only
    flips the reason, so without this arm the order is untested.
    """
    root = tmp_path / "tree"
    linked = root / "inside" / "linked"
    linked.mkdir(parents=True)
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    (linked / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    (linked / "theirs.md").write_text("# not ours\n", encoding="utf-8")

    registered = (str(linked.resolve()).lower(),)
    _files, skips = drift_guard._walk(root, worktrees=registered)  # noqa: SLF001
    reasons = {skip["path"]: skip["reason"] for skip in skips}

    assert reasons["inside/linked/"] == drift_guard.REGISTERED_WORKTREE_REASON, reasons


def test_the_default_asks_git_so_a_direct_caller_is_guarded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS-1153: the ``worktrees is None`` default is the WHOLE POINT of the item.

    Every other arm here passes a registration explicitly, so every other arm
    stays green when the default is cut to an empty tuple. This one builds a
    REAL linked worktree, deletes its marker the way `git worktree remove`
    does, and calls _walk with no argument at all.
    """
    from tests import conftest  # noqa: PLC0415 - the one git runner the suite owns
    from tests.git_env import relocates  # noqa: PLC0415

    for name in [key for key in os.environ if relocates(key)]:
        monkeypatch.delenv(name)

    root = tmp_path / "main"
    root.mkdir()
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    setup = (
        ("init", "--quiet"),
        ("config", "user.email", "suite@example.invalid"),
        ("config", "user.name", "suite"),
        ("config", "commit.gpgsign", "false"),
        ("add", "--", "top.md"),
        ("commit", "--quiet", "--no-verify", "-m", "base"),
        ("worktree", "add", "--quiet", "--detach", "inside/linked"),
    )
    for args in setup:
        proc = conftest.run_git(root, *args)
        if proc is None:
            pytest.skip("git is not installed, so no worktree can be registered")
        assert proc.returncode == 0, f"control: git {args[0]} exited {proc.returncode}"

    linked = root / "inside" / "linked"
    (linked / "theirs.md").write_text("# not ours\n", encoding="utf-8")
    # The teardown window: `git worktree remove` deletes the marker BEFORE the
    # files, and the registration outlives it.
    (linked / ".git").unlink()

    # The control. With the registration withheld, the walk DOES enter it - so a
    # green below is the default asking git, and not some unrelated prune.
    assert "inside/linked/theirs.md" in _walked(root, worktrees=())

    files, _skips = drift_guard._walk(root)  # noqa: SLF001 - NO argument. The point.
    walked = {path.relative_to(root).as_posix() for path in files}
    assert walked == {"top.md"}, walked


def test_every_pruned_path_is_ignored_by_git_and_tracks_nothing(
    repo_root: Path,
) -> None:
    """CS-1153: the set is graded against git, in the REAL tree, entry by entry.

    A superset assertion over the skip records cannot see an OVER-BROAD prune:
    widening an entry to `ops` or `shell` - both tracked, authored and graded -
    leaves every other arm here green. This one asks git, which is the only
    authority on what this tree owns, and grades the WEAKEST member rather than
    the population: a single entry that tracks a file fails it.
    """
    from tests import conftest  # noqa: PLC0415 - the one git runner the suite owns

    pruned = sorted(drift_guard.WALK_SKIP_ROOT_PATHS)
    # The anti-vacuity floor. A set narrowed to nothing satisfies every
    # assertion below by having no member to fail one.
    assert len(pruned) >= _PRUNED_PATH_FLOOR, pruned

    tracked: dict[str, str] = {}
    unignored: list[str] = []
    for relative in pruned:
        listing = conftest.run_git(repo_root, "ls-files", "--", relative)
        if listing is None:
            pytest.skip("git is not installed, so membership cannot be asked")
        assert listing.returncode == 0, relative
        if listing.stdout.strip():
            tracked[relative] = listing.stdout.decode("utf-8", "replace").splitlines()[0]
        ignored = conftest.run_git(repo_root, "check-ignore", "-q", "--", relative + "/")
        assert ignored is not None, relative
        assert ignored.returncode in (0, 1), (relative, ignored.returncode)
        if ignored.returncode != 0:
            unignored.append(relative)

    assert tracked == {}, tracked
    assert unignored == [], unignored


#: CS-1155 - the floor on WALK_SKIP_FILE_PATTERNS, one below the membership the
#: table shipped with, which is 7. Named rather than written at the assertion so
#: a future author moving it has to move a constant with a reason attached. An
#: adversary measured the first version of this constant at 3 against a table of
#: 3 while this comment claimed "one below": the control was stricter than it
#: said, which is the same rot as one that is looser.
_PRUNED_FILE_PATTERN_FLOOR = 6

#: CS-1155 - a SEPARATE floor, on the size of the git index read. It shares no
#: meaning with the constant above and an adversary found the two conflated: a
#: threshold of 3 against an observed 428 would let an index read collapse by
#: ninety-nine percent and still pass, leaving the only arm that is live on CI
#: grading almost nothing.
_INDEX_SIZE_FLOOR = 300


def _cs1155_tree(root: Path) -> None:
    """A tree carrying one file of every shape the FILE half must prune.

    Authored siblings sit beside each pruned file at the SAME path, so a rule
    that widened from the shape to its directory - `ops/loop/`, `.claude/` -
    fails by losing an authored file rather than by a bare count.
    """
    (root / "top.md").write_text("# clean\n", encoding="utf-8")

    # Unanchored shapes, at the root and again nested, because a NAME rule that
    # only fired at depth zero would pass a root-only arm.
    (root / "adj_node_floor.log").write_text("stack trace\n", encoding="utf-8")
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (root / ".claude" / "settings.local.json").write_text("{}\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "deep.md").write_text("# clean\n", encoding="utf-8")
    (root / "docs" / "nested.log").write_text("stack trace\n", encoding="utf-8")

    # The anchored path, beside the authored file the lane really tracks there.
    (root / "ops" / "loop").mkdir(parents=True)
    (root / "ops" / "loop" / "config.json").write_text("{}\n", encoding="utf-8")
    (root / "ops" / "loop" / "queue_loop.py").write_text("pass\n", encoding="utf-8")


def test_the_walk_prunes_a_gitignored_file_shape(tmp_path: Path) -> None:
    """CS-1155: _walk prunes DIRECTORIES and could not express a file shape.

    The walk over this repository therefore returned files `git ls-files` does
    not - among them a stray root .log, which .gitignore classifies as
    potentially PII-bearing for exactly the reason CS-1153 cited as its motive,
    and which the walk still handed to the character-set and secret readers.
    """
    root = tmp_path / "tree"
    root.mkdir()
    _cs1155_tree(root)

    assert _walked(root) == {
        "top.md",
        "docs/deep.md",
        ".claude/settings.json",
        "ops/loop/queue_loop.py",
    }


def test_the_walk_records_every_file_it_pruned_with_a_reason(tmp_path: Path) -> None:
    """CS-1155: a pruned FILE is reported the way a pruned directory is.

    The record's path carries NO trailing slash, which is the only thing in a
    skip record that distinguishes a file from a directory.
    """
    root = tmp_path / "tree"
    root.mkdir()
    _cs1155_tree(root)

    _files, skips = drift_guard._walk(root, worktrees=())  # noqa: SLF001
    reasons = {skip["path"]: skip["reason"] for skip in skips}

    assert set(reasons) >= {
        "adj_node_floor.log",
        "docs/nested.log",
        ".claude/settings.local.json",
        "ops/loop/config.json",
    }, reasons
    assert all(reasons[path] for path in reasons), reasons
    assert "adj_node_floor.log/" not in reasons, reasons


def test_an_anchored_file_pattern_does_not_match_a_deeper_path(tmp_path: Path) -> None:
    """CS-1155: an anchored pattern is a FILE, not a suffix to match anywhere.

    `.gitignore` anchors /ops/loop/config.json at the repository root. A
    matcher comparing only the tail would prune a same-named file under any
    vendored or nested `ops/loop/`, which this tree does not own the right to
    hide. The root copy in the same arm is the control: without it a matcher
    that pruned NOTHING would pass this by pruning nothing.
    """
    root = tmp_path / "tree"
    nested = root / "vendor" / "ops" / "loop"
    nested.mkdir(parents=True)
    (nested / "config.json").write_text("{}\n", encoding="utf-8")
    (root / "ops" / "loop").mkdir(parents=True)
    (root / "ops" / "loop" / "config.json").write_text("{}\n", encoding="utf-8")

    assert _walked(root) == {"vendor/ops/loop/config.json"}


def test_every_pruned_file_pattern_is_ignored_by_git_and_tracks_nothing(
    repo_root: Path,
) -> None:
    """CS-1155: the file table is graded against git, entry by entry.

    The weakest member decides, not the population: one pattern matching a
    tracked file fails this. Widening `*.log` to `*.json`, or anchoring the
    lane's config entry one segment shorter, hides authored files from every
    reader downstream and leaves every synthetic arm above green.
    """
    from tests import conftest  # noqa: PLC0415 - the one git runner the suite owns

    patterns = sorted(drift_guard.WALK_SKIP_FILE_PATTERNS)
    # The anti-vacuity floor. A table narrowed to nothing satisfies every
    # assertion below by having no member to fail one.
    assert len(patterns) >= _PRUNED_FILE_PATTERN_FLOOR, patterns

    listing = conftest.run_git(repo_root, "ls-files")
    if listing is None:
        pytest.skip("git is not installed, so membership cannot be asked")
    assert listing.returncode == 0
    index = [line for line in listing.stdout.decode("utf-8", "replace").splitlines() if line]
    # The control. An empty index read makes the tracked half below vacuous by
    # having nothing for a pattern to collide with.
    assert len(index) >= _INDEX_SIZE_FLOOR, len(index)

    tracked: dict[str, str] = {}
    unignored: list[str] = []
    for pattern in patterns:
        # Matched here rather than by a pathspec, and CASE-INSENSITIVELY. A
        # pathspec is case-sensitive, so it would miss exactly the divergence
        # the floor's fnmatchcase choice creates - and an over-broad entry that
        # collided with `README.MD` rather than `README.md` would read clean.
        for entry in index:
            subject = entry if "/" in pattern else entry.rsplit("/", 1)[-1]
            if fnmatch.fnmatch(subject.lower(), pattern.lower()):
                tracked[pattern] = entry
                break
        # A pattern is a shape, and check-ignore wants a path - so ask it about
        # the shortest path the shape describes.
        sample = pattern.replace("*", "sample")
        ignored = conftest.run_git(repo_root, "check-ignore", "-q", "--", sample)
        assert ignored is not None, pattern
        assert ignored.returncode in (0, 1), (pattern, ignored.returncode)
        if ignored.returncode != 0:
            unignored.append(pattern)

    assert tracked == {}, tracked
    assert unignored == [], unignored


def test_the_walk_reaches_every_tracked_file_in_this_repository(
    repo_root: Path,
) -> None:
    """CS-1155: the difference is DERIVED from git, so it cannot go stale.

    Two directions, and they fail for opposite reasons.

    MISSING - a tracked file the walk never reached - is an OVER-BROAD rule,
    and it is live on every platform and in every fresh clone, because tracked
    files exist everywhere.

    EXTRA - a walked file the index does not carry - is the CS-1155 defect
    itself. It is only observable where an ignored file is actually on disk, so
    on a fresh CI checkout this half has nothing to see. It is asserted anyway
    rather than skipped: the primary tree is where the residue accumulates, and
    a list written down here instead would be the stale thing this arm exists
    to avoid.
    """
    from tests import conftest  # noqa: PLC0415 - the one git runner the suite owns

    listing = conftest.run_git(repo_root, "ls-files")
    if listing is None:
        pytest.skip("git is not installed, so the index cannot be asked")
    assert listing.returncode == 0
    indexed = {
        line
        for line in listing.stdout.decode("utf-8", "replace").splitlines()
        if line and (repo_root / line).is_file()
    }
    # The control. An index read that came back empty would make both
    # differences vacuous, and the MISSING half would grade nothing.
    assert len(indexed) >= _INDEX_SIZE_FLOOR, len(indexed)

    # _ASK_GIT, so the walk asks git itself - the whole point of the repair.
    # An adversary measured the worktrees argument here as inert and it is kept
    # only because a real tree deserves the real value.
    walked = _walked(
        repo_root,
        worktrees=drift_guard._registered_worktrees(repo_root),  # noqa: SLF001
        ignored=_ASK_GIT,
    )
    missing = sorted(indexed - walked)
    extra = sorted(walked - indexed)

    assert missing == [], missing
    assert extra == [], extra


def _cs1155_repo(root: Path, ignore_body: str) -> bool:
    """Build a REAL git repository at ``root`` carrying ``ignore_body``.

    Returns False when git is not installed, so the caller skips rather than
    asserting against an authority that was never asked.
    """
    from tests import conftest  # noqa: PLC0415 - the one git runner the suite owns
    from tests.git_env import relocates  # noqa: PLC0415

    for name in [key for key in os.environ if relocates(key)]:
        os.environ.pop(name, None)
    root.mkdir(parents=True, exist_ok=True)
    (root / ".gitignore").write_text(ignore_body, encoding="utf-8")
    for args in (
        ("init", "--quiet"),
        ("config", "user.email", "suite@example.invalid"),
        ("config", "user.name", "suite"),
        ("config", "commit.gpgsign", "false"),
    ):
        proc = conftest.run_git(root, *args)
        if proc is None:
            return False
        assert proc.returncode == 0, f"control: git {args[0]} exited {proc.returncode}"
    return True


def test_the_floor_prunes_a_save_file_shape(tmp_path: Path) -> None:
    """CS-1155: a .sav is a save file, and CLAUDE.md 11 forbids enumerating one.

    The first version of the file table held three entries - the three that
    happened to be lying on the development machine's disk on the day it was
    written. An adversary put a `.sav` beside them and walked it straight
    through. Its membership is a CLASS now, not a residue: every shape this
    repository classifies as personal data or credential material.
    """
    root = tmp_path / "tree"
    root.mkdir()
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    (root / "world.sav").write_bytes(b"\x00save\x00")
    (root / "server.pem").write_text("KEY\n", encoding="utf-8")
    (root / ".env").write_text("TOKEN=x\n", encoding="utf-8")
    (root / ".mcp.json").write_text("{}\n", encoding="utf-8")

    # ignored=frozenset() - the FLOOR alone, with git's answer withheld. Without
    # that this arm would pass on a machine where git happened to answer.
    assert _walked(root, ignored=None) == {"top.md"}


def test_the_floor_prunes_a_directory_a_shape_names(tmp_path: Path) -> None:
    """CS-1155: a shape cannot tell a file from a directory, and nor can git.

    `.gitignore`'s `*.log` ignores a directory called `notes.log` and
    everything under it. The first version of this rule consulted the file half
    for FILES alone, so an adversary walked a file beneath one through it -
    the PII class the item was filed over, arriving by the other shape.
    """
    root = tmp_path / "tree"
    (root / "notes.log").mkdir(parents=True)
    (root / "notes.log" / "inner.txt").write_text("parsed bytes\n", encoding="utf-8")
    (root / "keep.md").write_text("# clean\n", encoding="utf-8")

    _files, skips = drift_guard._walk(  # noqa: SLF001
        root, worktrees=(), ignored=None
    )
    reasons = {skip["path"]: skip["reason"] for skip in skips}

    assert _walked(root, ignored=None) == {"keep.md"}
    assert reasons["notes.log/"] == drift_guard.WALK_SKIP_FILE_PATTERNS["*.log"], reasons


def test_the_floor_folds_case_the_same_way_on_every_runner(
    tmp_path: Path,
) -> None:
    """CS-1155, reversed by CS-1158 repair 3: the floor FOLDS case, host-independently.

    CS-1155 made the floor case-sensitive because `fnmatch` folds case under
    the HOST's rules, and a floor whose membership depends on the runner cannot
    be a floor. The cost it accepted - the floor alone did not prune
    `STRAY.LOG` - turned out to be a leak: an adjudicator measured `ZQ.LOG` and
    `ZQ.PEM` printing by name with git unreachable. The floor now folds by an
    explicit lower() on both sides, which reads no host setting, so the
    population is still the same on every runner and is now the wider one.

    Live against both regressions: dropping the fold keeps `STRAY.LOG` here,
    and swapping in `fnmatch` keeps it on every case-sensitive runner.
    """
    root = tmp_path / "tree"
    root.mkdir()
    (root / "keep.md").write_text("# clean\n", encoding="utf-8")
    (root / "quiet.log").write_text("lower\n", encoding="utf-8")
    (root / "STRAY.LOG").write_text("upper\n", encoding="utf-8")

    # keep.md is the control: a floor that pruned EVERYTHING would satisfy the
    # upper-case half for the wrong reason.
    assert _walked(root, ignored=None) == {"keep.md"}


def test_git_decides_case_and_the_walk_follows_it(tmp_path: Path) -> None:
    """CS-1155: parity is with GIT, which is not the same as a fixed population.

    core.ignorecase is true on a Windows checkout and false on a Linux one, so
    `STRAY.LOG` is ignored on one and tracked-able on the other. The walk must
    agree with git on BOTH, which means this arm cannot assert a population -
    it asserts the AGREEMENT, and asks git which side of it to expect.

    An adversary measured the first version walking `STRAY.LOG` while
    `git check-ignore` named it ignored, on this machine, with no arm seeing it.
    """
    from tests import conftest  # noqa: PLC0415 - the one git runner the suite owns

    root = tmp_path / "repo"
    if not _cs1155_repo(root, "*.log\n"):
        pytest.skip("git is not installed, so its answer cannot be asked")
    (root / "keep.md").write_text("# clean\n", encoding="utf-8")
    (root / "STRAY.LOG").write_text("upper\n", encoding="utf-8")

    verdict = conftest.run_git(root, "check-ignore", "-q", "--", "STRAY.LOG")
    assert verdict is not None
    assert verdict.returncode in (0, 1), verdict.returncode
    git_ignores_it = verdict.returncode == 0

    walked = _walked(root, ignored=_ASK_GIT)
    assert ("STRAY.LOG" in walked) is not git_ignores_it, (walked, git_ignores_it)
    # The control. A walk that returned nothing at all would satisfy the line
    # above whenever git said ignored.
    assert "keep.md" in walked, walked


def test_git_prunes_a_shape_the_floor_does_not_carry(tmp_path: Path) -> None:
    """CS-1155: the authority is git, and the table is only the floor.

    An adversary's sharpest finding was that a table of shapes copied out of
    .gitignore is a restatement CLAUDE.md section 4 forbids, and that it can
    fall arbitrarily far behind its source with every arm still green. The
    answer is not a longer table. It is to ask git, which answers with no
    commits at all - the case this walk exists for - and to keep the table as
    the floor for a tree where git cannot be reached.
    """
    root = tmp_path / "repo"
    if not _cs1155_repo(root, "hoard.txt\nvendored/\n"):
        pytest.skip("git is not installed, so its answer cannot be asked")
    (root / "keep.md").write_text("# clean\n", encoding="utf-8")
    (root / "hoard.txt").write_text("ignored\n", encoding="utf-8")
    (root / "vendored").mkdir()
    (root / "vendored" / "theirs.md").write_text("# theirs\n", encoding="utf-8")

    # The control: no shape in the floor names either, so with git's answer
    # withheld the walk collects both. Without this the arm below passes on a
    # walk that pruned them for some unrelated reason.
    assert _walked(root, ignored=None) == {
        ".gitignore",
        "keep.md",
        "hoard.txt",
        "vendored/theirs.md",
    }

    _files, skips = drift_guard._walk(root, worktrees=())  # noqa: SLF001
    reasons = {skip["path"]: skip["reason"] for skip in skips}

    assert _walked(root, ignored=_ASK_GIT) == {".gitignore", "keep.md"}
    assert reasons["hoard.txt"] == drift_guard.GITIGNORED_REASON, reasons
    assert reasons["vendored/"] == drift_guard.GITIGNORED_REASON, reasons


def test_git_answers_a_repository_with_no_commits(tmp_path: Path) -> None:
    """CS-1155: the walk is the fallback for an EMPTY INDEX, so this is the case.

    `enumerate_files` reaches the walk only when `git ls-files` came back empty
    - a scaffold before commit one. If the new authority needed a commit it
    would answer nothing precisely where it is needed, and the floor would be
    carrying the whole rule while the docstring claimed otherwise.
    """
    from tests import conftest  # noqa: PLC0415 - the one git runner the suite owns

    root = tmp_path / "repo"
    if not _cs1155_repo(root, "hoard.txt\n"):
        pytest.skip("git is not installed, so its answer cannot be asked")
    (root / "hoard.txt").write_text("ignored\n", encoding="utf-8")

    # The control: the index really is empty, which is what makes this the
    # fallback case rather than an ordinary repository.
    listing = conftest.run_git(root, "ls-files")
    assert listing is not None
    assert listing.stdout.strip() == b"", listing.stdout

    assert drift_guard._git_ignored(root) == frozenset({"hoard.txt"})  # noqa: SLF001


def test_git_unreachable_leaves_the_floor_alone_deciding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS-1155: an unreachable git is the git-LESS case, never an error.

    _git_ignored answers with an empty set on all four soft paths, and the walk
    then prunes by the floor alone. A version that raised, or that treated the
    empty answer as "nothing is ignored, so collect the save file", would turn
    a missing tool into a non-negotiable-11 breach.
    """
    root = tmp_path / "tree"
    root.mkdir()
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    (root / "world.sav").write_bytes(b"\x00save\x00")

    monkeypatch.setattr(drift_guard, "resolve_tool", lambda _name: None)

    # The control: with git resolved away, the authority really is silent.
    assert drift_guard._git_ignored(root) is None  # noqa: SLF001
    # _ASK_GIT, so the walk asks - and gets nothing, and prunes anyway.
    assert _walked(root, ignored=_ASK_GIT) == {"top.md"}


def test_a_slashed_pattern_carrying_a_wildcard_still_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CS-1155: the matcher's contract, graded rather than asserted in a comment.

    The first version compared a slashed pattern by string EQUALITY and a
    comment told a future author there was no third case to get wrong.
    `.gitignore` already carries one - `/memory/*.db` - which equality would
    silently never match. No such pattern is in the table today, so the arm
    installs one: the contract is what is being graded, not the membership.
    """
    monkeypatch.setattr(
        drift_guard,
        "WALK_SKIP_FILE_PATTERNS",
        MappingProxyType({"memory/*.db": "local-only - the recall mirror"}),
    )
    reason = drift_guard._skip_file_reason(  # noqa: SLF001
        "memory/recall.db", "recall.db", None
    )

    assert reason == "local-only - the recall mirror"
    # Still anchored: the pattern is a path, not a tail to find anywhere.
    assert (
        drift_guard._skip_file_reason(  # noqa: SLF001
            "vendor/memory/recall.db", "recall.db", None
        )
        is None
    )


def test_the_floor_never_overrules_an_answer_git_gave(tmp_path: Path) -> None:
    """CS-1155: where git ANSWERED, git decides. The adjudicator's finding.

    The first repair consulted the floor first, so on a tree where `build.log`
    was TRACKED and git ignored nothing, the walk dropped it anyway. That made
    the sentence the whole design rests on - the table is only the floor for a
    tree with no git - false, and it is the sentence that answered a section-4
    restatement objection three adversaries raised.

    An EMPTY answer is still an answer. That is why this arm passes
    `frozenset()` rather than None, and why _git_ignored returns None for a git
    it could not ask: collapsing the two is the defect.
    """
    root = tmp_path / "tree"
    root.mkdir()
    (root / "keep.md").write_text("# clean\n", encoding="utf-8")
    (root / "build.log").write_text("tracked, despite the shape\n", encoding="utf-8")

    # The control: with git UNREACHABLE the floor does decide, and prunes it.
    # Without this the arm below passes on a floor that matched nothing at all.
    assert _walked(root, ignored=None) == {"keep.md"}

    assert _walked(root, ignored=frozenset()) == {"keep.md", "build.log"}


def test_the_floor_names_the_class_for_a_path_git_also_named(tmp_path: Path) -> None:
    """CS-1155: the two authorities COLLIDE here, and the reason identity decides.

    Swapping the two lookups was a silent mutant that survived every arm,
    because no fixture made both authorities name the same path: the floor arms
    withheld git, and the git arms used shapes the floor does not carry. The
    reason is the GROUPING KEY of the rendered skip list, so a swap collapses
    every personal-data and credential class into one generic bucket.
    """
    root = tmp_path / "repo"
    if not _cs1155_repo(root, "*.log\n*.sav\nhoard.txt\n"):
        pytest.skip("git is not installed, so its answer cannot be asked")
    (root / "quiet.log").write_text("both authorities name this\n", encoding="utf-8")
    (root / "world.sav").write_bytes(b"\x00save\x00")
    (root / "hoard.txt").write_text("git alone names this\n", encoding="utf-8")

    _files, skips = drift_guard._walk(root, worktrees=())  # noqa: SLF001
    reasons = {skip["path"]: skip["reason"] for skip in skips}

    # The collision: git names it AND the floor classifies it. The floor's
    # reason wins, because it says WHICH class and git's says only "ignored".
    assert reasons["quiet.log"] == drift_guard.WALK_SKIP_FILE_PATTERNS["*.log"], reasons
    assert reasons["world.sav"] == drift_guard.WALK_SKIP_FILE_PATTERNS["*.sav"], reasons
    # The control. Without a path git alone names, an implementation that
    # ignored git entirely would satisfy both lines above.
    assert reasons["hoard.txt"] == drift_guard.GITIGNORED_REASON, reasons


@pytest.mark.parametrize("ignorecase", ["true", "false"])
def test_git_decides_case_on_either_kind_of_checkout(tmp_path: Path, ignorecase: str) -> None:
    """CS-1155: the case arm, made live on BOTH runners rather than on this one.

    The unparametrized version asked git what it thought and asserted the walk
    agreed. On a case-FOLDING checkout that is a real grading. On a
    case-sensitive one - every ubuntu runner, and tier 1 is ubuntu only - git
    says not-ignored, the walk keeps the file, and a walk that pruned NOTHING
    satisfies both the assertion and its own control. An adversary measured
    exactly that, which is the CS-1156 lesson arriving from the other side: a
    control can grade the platform by being SATISFIED everywhere but one.

    core.ignorecase is a config value, not a filesystem property, so both arms
    run on both runners.
    """
    from tests import conftest  # noqa: PLC0415 - the one git runner the suite owns

    root = tmp_path / "repo"
    if not _cs1155_repo(root, "*.log\n"):
        pytest.skip("git is not installed, so its answer cannot be asked")
    setting = conftest.run_git(root, "config", "core.ignorecase", ignorecase)
    assert setting is not None
    assert setting.returncode == 0, ignorecase
    (root / "keep.md").write_text("# clean\n", encoding="utf-8")
    (root / "quiet.log").write_text("lower\n", encoding="utf-8")
    (root / "STRAY.LOG").write_text("upper\n", encoding="utf-8")

    verdict = conftest.run_git(root, "check-ignore", "-q", "--", "STRAY.LOG")
    assert verdict is not None
    assert verdict.returncode in (0, 1), verdict.returncode
    git_ignores_it = verdict.returncode == 0
    # The control that the earlier version lacked: this arm only grades
    # anything if the two settings actually disagree somewhere, so each one
    # states what it expects of git rather than accepting either answer.
    assert git_ignores_it is (ignorecase == "true"), (ignorecase, git_ignores_it)

    walked = _walked(root, ignored=_ASK_GIT)
    assert ("STRAY.LOG" in walked) is not git_ignores_it, (walked, git_ignores_it)
    # The lower-case sibling is pruned on BOTH settings, so a walk that pruned
    # nothing cannot satisfy the case-sensitive arm.
    assert walked == {".gitignore", "keep.md"} | (set() if git_ignores_it else {"STRAY.LOG"}), (
        walked
    )
