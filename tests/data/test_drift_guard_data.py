"""Tests for the version-pin guard in tools/drift_guard.py - guard (h).

THE CRITERION THIS MODULE GRADES, verbatim from ROADMAP.md CS-200: "the drift
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
"""

from __future__ import annotations

import errno
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

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


def make_repo(root: Path, *, with_pin: bool = True) -> Path:
    """Build the smallest tree every drift guard reports PASS or WARN on.

    Guards (a) through (g) each need something in the tree, and any one of them
    failing would make an exit-code assertion about guard (h) meaningless. So
    the tree carries a budgeted CLAUDE.md with a frozen-file section, a
    CONVENTIONS section 2 ownership table naming one file that exists, a memory
    index with no leaves, and a fully covered port band.

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
    return root


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
    assert code == 0
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
    assert needles, "the oracle derived no needles, so the privacy test below proves nothing"

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
