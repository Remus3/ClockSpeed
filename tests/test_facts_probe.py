"""Tests for tools/facts_probe.py - the SessionStart live-state probe.

WHAT THIS MODULE GRADES, verbatim from ROADMAP.md CS-203: "a test asserts the
default output carries no account id, no world name and no home path, and that
the `--unredacted` opt-in is the only path that emits them." The probe was
migrated onto clockspeed/data/locate.py and its schema bumped to 2 during phase
2 with no automated coverage at all, so until this file existed the only
evidence it redacted anything was that somebody had run it once and read the
line.

THE ORACLE IS NEVER THE CODE UNDER TEST. ``redact(x) != x`` looks like a test
for "x held personal data" and is not one - it reports whatever the redactor
happens to recognise, so a redactor with a blind spot grades itself clean on
exactly the strings it cannot see (CONVENTIONS.md section 15.1). Every value
asserted on below is synthetic, is placed into a temporary tree by this file,
and is therefore known to be present as ground truth before the probe is ever
called. Nothing is asked of locate.redact() to decide what a leak is.

BOTH HALVES ARE ASSERTED, and the negative half is not decoration. A probe that
emitted nothing at all would satisfy every "the account id is absent" assertion
in this file. The --unredacted tests are what stop that: they require the very
same synthetic values to be PRESENT, so the pair pins "redacted by default" and
"the opt-in actually opts in" rather than "the output is empty".

BOTH RENDERINGS ARE ASSERTED. A value can be absent from a parsed field and
still present in the line the hook injects - a stray key, a resolver label, a
diagnostic. So the schema-2 payload is checked field by field AND the exact
string main() prints is swept for the same synthetic values.

PRIVACY (CLAUDE.md non-negotiables 3, 11 and 12). No real account id, no real
world name, no real Windows account name and no real home path appears in this
file or in any assertion. The account-id-shaped, hex-token-shaped and
GUID-shaped strings below are invented here. The account-directory shapes
deliberately share no character class: an all-digit rule matches one of them,
which is precisely how a redactor comes to be "fixed" for one platform and
silent for the other three.

NO GAME, NO SAVE DIRECTORY, NO LOCALAPPDATA. Every test points all four
CLOCKSPEED_* overrides at paths under tmp_path, so the operator's real install
and real save directory can never answer and the suite behaves identically on
the ubuntu CI runner that has neither.

THE GIT FACTS ARE COVERED BY A REAL REPOSITORY, not by a stub. ``git.branch``
and ``git.hooks_path`` are whatever ``git`` says they are, so the tests for
them build a throwaway repository under the synthetic home with ``git init``
and set ``core.hooksPath`` with ``git config`` - the same shape
tests/test_precommit_gate.py uses. Stubbing _git() would have tested this
file's idea of what git returns; planting the value in git itself tests the
path the SessionStart hook actually runs.

WHAT THIS FILE STILL DOES NOT COVER, stated so nobody reads it as covering
more.

  - ``git.sha`` is emitted exactly as git gave it, deliberately. A short SHA is
    machine-generated hex, it cannot carry a path, and redacting it would let
    the digit-run backstop in locate.redact() eat an all-numeric abbreviation.
    Nothing below asserts anything about its content.
  - ``game.build`` and ``game.build_via`` are read from the publisher's shipped
    binaries and from a fixed set of literal labels, so no test here plants a
    value in them. On a machine with no install - which is every machine this
    suite runs on, because the autouse fixture guarantees it - they are the
    constants "unknown" and "no install".
  - locate.redact() builds its home needles from the ENVIRONMENT. A hooks path
    that is neither inside the checkout nor under any directory the environment
    names - a shared hooks directory on another volume, say - is rendered by
    whatever needles do match, and this file plants nothing of that shape. That
    is a property of the redactor (clockspeed/data/locate.py), not of the probe,
    and it is why the probe prefers a repo-relative rendering where one exists
    rather than relying on redaction alone.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, NamedTuple

import pytest

from clockspeed.data import locate

REPO_ROOT = Path(__file__).resolve().parents[1]
FACTS_PROBE_SOURCE = REPO_ROOT / "tools" / "facts_probe.py"

# ---------------------------------------------------------------------------
# Synthetic fixture material - every byte of it invented here
# ---------------------------------------------------------------------------

# Account-id shaped and 17 digits like a platform id. These are not anybody's
# account ids; they exist so the count, the ordering and the redaction rules
# can be exercised without a real one ever entering the repository.
NEWEST_FAKE_ACCOUNT_ID = "40000000000000004"
OLDEST_FAKE_ACCOUNT_ID = "50000000000000005"
FAKE_ACCOUNT_IDS = (NEWEST_FAKE_ACCOUNT_ID, OLDEST_FAKE_ACCOUNT_ID)

# A world name is operator-chosen and is personal data (CLAUDE.md rule 3), and
# a save file is named after it, so the filename carries it into every path.
FAKE_WORLD_NAME = "SyntheticProbeWorldName"
FAKE_SAVE_FILENAME = f"{FAKE_WORLD_NAME}_autosave_0.sav"

# Not a real save. A save file is a personal-data-bearing artifact and never
# goes near this repository (CLAUDE.md non-negotiable 11); what the probe needs
# is a file with that suffix, so that is all this is.
SYNTHETIC_SAVE_BYTES = b"synthetic bytes - not a save file\n"

# The directory name standing in for the operator's profile directory. Chosen
# so it is not a substring of any value asserted on below: locate.redact()
# turns the home directory's own NAME into a needle, and a name that collided
# with a synthetic account id would redact it for the wrong reason.
FAKE_HOME_DIR_NAME = "synthetic-profile-dir"

# The three account-directory shapes that actually occur, none of them
# resembling any real platform's prefix and none sharing a character class with
# the others. Only the seventeen-digit shape is reachable by the digit-run
# backstop in locate.redact(); the other two can only be caught by POSITION,
# which is the property these parametrized cases exist to pin.
ACCOUNT_DIR_SHAPES: tuple[tuple[str, str], ...] = (
    ("hex-token", "b7c8d9e0f1a2b3c4d5e6f708192a3b4c"),
    ("braceless-guid", "7d3b0a12-4c65-4e88-b1f2-90ac6de5f431"),
    ("seventeen-digit", NEWEST_FAKE_ACCOUNT_ID),
)

# The schema version this file is written against. A DELIBERATE PIN, not a
# restated fact: tools/facts_probe.py bumps this field precisely so a shape
# change with the version left alone becomes visible, and a test that read the
# version out of the payload it is grading could never see that happen.
EXPECTED_SCHEMA = 2

# What a redacted save root reads as, quoted from the probe's own module
# docstring (tools/facts_probe.py: "the SHAPE of the answer").
LOCALAPPDATA_PLACEHOLDER = "<localappdata>"

# The other two tokens locate.redact() substitutes, named here for the same
# reason LOCALAPPDATA_PLACEHOLDER is: a test that asked the redactor which
# token it was going to emit would be using the code under test as its oracle.
HOME_PLACEHOLDER = "<home>"
USER_PLACEHOLDER = "<user>"

# The synthetic checkout the git-facts tests run a real `git init` in. It sits
# UNDER the synthetic home, because "a checkout under a home directory" is the
# exact condition the acceptance criterion names.
SYNTHETIC_CHECKOUT_DIR_NAME = "synthetic-checkout"

# The hooks directory name scripts/install_hooks.py wires, and a second one
# planted OUTSIDE the checkout. The two take different routes through the
# probe - one is repo-relative, one can only be redacted - so both are planted.
HOOKS_DIR_NAME = ".githooks"
SHARED_HOOKS_DIR_NAME = "shared-githooks"

# A branch named after the account directory, which is an ordinary convention
# ("<user>/wip") and is why a branch name is swept at all. Git's ref format
# forbids the backslash, the colon and the space, so a branch can never BE an
# absolute Windows path - but the Windows account name is personal data
# (CLAUDE.md non-negotiable 3) every bit as much as a home path is, and this is
# the shape that carries it. FAKE_HOME_DIR_NAME is the profile directory's own
# name, which locate.redact() turns into a <user> needle.
SYNTHETIC_BRANCH = FAKE_HOME_DIR_NAME + "/wip"
REDACTED_BRANCH = USER_PLACEHOLDER + "/wip"

# What an operator-controlled string renders as when the redactor could not be
# imported. Pinned here rather than read from facts_probe, for the same reason
# EXPECTED_SCHEMA is: a test that asked the module under test which token it
# was about to emit could never see that token change.
WITHHELD_PLACEHOLDER = "<withheld>"

GIT_TIMEOUT = 30


def _load_facts_probe() -> ModuleType:
    """Load tools/facts_probe.py by path.

    tools/ is not an importable package - it is a directory of entry-point
    scripts - so the module is loaded from its file, the same way
    tests/data/test_drift_guard_data.py loads tools/drift_guard.py.

    Returns:
        The loaded module.

    Raises:
        ImportError: The file could not be turned into a module.
    """
    spec = importlib.util.spec_from_file_location("clockspeed_facts_probe", FACTS_PROBE_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {FACTS_PROBE_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


facts_probe = _load_facts_probe()


class FakeMachine(NamedTuple):
    """A synthetic machine the probe can be pointed at.

    Every field is a path this file created under tmp_path. Holding them here
    rather than recomputing them in each test is what makes the assertions
    ground truth: the test knows what it planted, so it never has to ask the
    redactor whether a string was personal data.
    """

    home: Path
    local: Path
    save_root: Path
    game_dir: Path
    account_dirs: tuple[Path, ...]
    save_file: Path

    def __repr__(self) -> str:
        """Render without any path, because a failure header is an echo path.

        pytest reprs every fixture value it can reach at the top of a failure
        report. tmp_path lives under the operator's real profile directory, so
        the default tuple repr would print their account name into the CI log
        on the very run that proves it must not be printed (CLAUDE.md
        non-negotiable 12). The fields stay readable to the test; only the
        rendering is withheld.
        """
        return f"<FakeMachine with {len(self.account_dirs)} account dir(s), paths withheld>"


# ---------------------------------------------------------------------------
# Isolation
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _detached_from_this_machine(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Detach every resolver from the operator's install, saves and config.

    All four overrides are SET to paths under tmp_path rather than deleted. An
    override naming a missing directory resolves to None instead of falling
    through to auto-detection, so a machine with the game installed and a
    machine that has never seen it produce the same answer here. Deleting them
    would let auto-detection find the real install and the real save root, and
    every privacy assertion below would then be running against the operator's
    own data.

    USERPROFILE and LOCALAPPDATA are pointed at synthetic directories for the
    same reason: locate.redact() builds its needles from them on every call, so
    a test that left them alone would be grading the redactor against this
    machine's account name rather than against a value it controls.

    The account-directory memory is replaced with a fresh empty list. The
    resolver remembers the names it hands out so redact() can strip an override
    that points outside the save root, and that memory is module state - left
    alone, one test's synthetic account name stays a redaction needle for the
    next test, and a later "it did not leak" assertion could pass because of a
    neighbour rather than because of the code. Replacing the ATTRIBUTE through
    monkeypatch restores it afterwards, which calling a reset helper would not.
    """
    for name in (
        locate.ENV_GAME_DIR,
        locate.ENV_SAVE_ROOT,
        locate.ENV_ACCOUNT_DIR,
        locate.ENV_LOCAL_CONFIG,
    ):
        monkeypatch.setenv(name, str(tmp_path / "absent" / name.lower()))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / FAKE_HOME_DIR_NAME))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / FAKE_HOME_DIR_NAME / "AppData" / "Local"))
    monkeypatch.setattr(locate, "_RESOLVED_ACCOUNT_NAMES", [])


@pytest.fixture
def machine(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> FakeMachine:
    """Build a synthetic install and save tree and point the probe at both.

    The tree has the real shape: a save root at
    ``<home>/AppData/Local/FactoryGame/Saved/SaveGames`` holding two account
    directories, with one save file named after a world inside the newer of
    them. That is every category of personal data the probe can reach - a home
    path, an account id and a world name - planted at once.
    """
    home = tmp_path / FAKE_HOME_DIR_NAME
    local = home / "AppData" / "Local"
    save_root = local.joinpath(*locate.SAVE_ROOT_PARTS)
    save_root.mkdir(parents=True)

    account_dirs = []
    for name in FAKE_ACCOUNT_IDS:
        account_dir = save_root / name
        account_dir.mkdir()
        account_dirs.append(account_dir)

    save_file = account_dirs[0] / FAKE_SAVE_FILENAME
    save_file.write_bytes(SYNTHETIC_SAVE_BYTES)

    game_dir = home / "Games" / "SyntheticInstall"
    game_dir.mkdir(parents=True)

    monkeypatch.setenv(locate.ENV_SAVE_ROOT, str(save_root))
    monkeypatch.setenv(locate.ENV_GAME_DIR, str(game_dir))
    return FakeMachine(
        home=home,
        local=local,
        save_root=save_root,
        game_dir=game_dir,
        account_dirs=tuple(account_dirs),
        save_file=save_file,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def probe_payload(*, unredacted: bool = False) -> dict[str, Any]:
    """Run the probe and return its schema-2 payload."""
    payload: dict[str, Any] = facts_probe.probe(unredacted=unredacted)
    return payload


def run_main(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str]:
    """Run the command-line entry point and return its exit code and printed line."""
    code: int = facts_probe.main(list(args))
    return code, capsys.readouterr().out


def personal_values(machine: FakeMachine) -> dict[str, str]:
    """Every synthetic string the probe must not emit by default, labelled.

    Labels rather than a bare list so a failure names WHICH category leaked.
    All of it is ground truth planted by the ``machine`` fixture, so a value
    appearing in the output is a leak by construction and not by the opinion of
    the redactor.
    """
    values = {
        "world name": FAKE_WORLD_NAME,
        "save filename": FAKE_SAVE_FILENAME,
        "home path (posix)": machine.home.as_posix(),
        "home path (native)": str(machine.home),
    }
    for index, account_id in enumerate(FAKE_ACCOUNT_IDS):
        values[f"account id {index}"] = account_id
    return values


def assert_absent(rendered: str, machine: FakeMachine) -> None:
    """Assert no synthetic personal value survives into ``rendered``.

    LABELS, never the values. Binding the offending strings to a local is
    enough to publish them - pytest reprs every local it can reach in the
    assert line of a failure - so the message names which category leaked and
    the leaked text itself stays out of the report.
    """
    lowered = rendered.lower()
    leaked = sorted(
        label for label, value in personal_values(machine).items() if value.lower() in lowered
    )
    assert not leaked, f"the redacted output leaked: {', '.join(leaked)}"


def assert_present(rendered: str, label: str, value: str) -> None:
    """Assert an opt-in rendering really did emit ``value``, without echoing it.

    The counterpart to :func:`assert_absent`. The result is reduced to a bool
    before the assert so neither the value nor the surrounding output reaches
    the failure report - an --unredacted payload is personal data by
    definition, and a failing test is not a licence to print it.
    """
    emitted = value in rendered
    assert emitted, f"the --unredacted output did not emit the {label}"


def assert_not_the_raw_path(emitted: object, raw: Path, field: str) -> None:
    """Assert a default-path field is something other than the raw path.

    Reduced to a bool for the same reason: on failure the field holds exactly
    the absolute path the assertion exists to keep out of the output.
    """
    unredacted_leak = emitted == raw.as_posix()
    assert not unredacted_leak, f"{field} carried the raw path on the default path"


def tree_snapshot(root: Path) -> dict[str, tuple[bool, int, int]]:
    """Record every entry under ``root`` as (is_dir, size, mtime_ns).

    A created, deleted, truncated or rewritten entry changes this mapping, and
    so does a write into the directory itself, because adding or removing a
    child moves the parent's mtime. Reading does not.
    """
    snapshot: dict[str, tuple[bool, int, int]] = {}
    for path in [root, *sorted(root.rglob("*"))]:
        stat = path.stat()
        key = "." if path == root else path.relative_to(root).as_posix()
        snapshot[key] = (path.is_dir(), stat.st_size, stat.st_mtime_ns)
    return snapshot


# ---------------------------------------------------------------------------
# The CS-203 acceptance criterion - the default path
# ---------------------------------------------------------------------------


def test_default_payload_carries_no_account_id_no_world_name_and_no_home_path(
    machine: FakeMachine,
) -> None:
    """The criterion itself, asserted against values this test planted.

    Positive assertions accompany the negative ones deliberately. A negative
    assertion rules out without pinning down (CONVENTIONS.md section 7.2): a
    probe that emitted an empty object would satisfy every "absent" line here,
    so the counts and the redacted rendering are pinned in the same breath.
    """
    payload = probe_payload()

    assert_absent(json.dumps(payload), machine)

    assert payload["redacted"] is True
    assert payload["save"]["root"] is True
    assert payload["save"]["accounts"] == len(FAKE_ACCOUNT_IDS)
    assert payload["save"]["savs"] == 1
    assert payload["save"]["newest"] is not None
    assert payload["game"]["found"] is True
    assert payload["game"]["dir"] is not None

    # The SHAPE of the answer, quoted from the probe's own module docstring.
    expected_root = LOCALAPPDATA_PLACEHOLDER + "/" + "/".join(locate.SAVE_ROOT_PARTS)
    shaped = payload["save"]["root_path"] == expected_root
    assert shaped, f"the redacted save root did not render as {expected_root}"
    assert_not_the_raw_path(payload["game"]["dir"], machine.game_dir, "game.dir")


def test_default_payload_withholds_the_account_names_and_the_newest_save_filename(
    machine: FakeMachine,
) -> None:
    """Two fields are withheld outright rather than redacted to a token.

    An account directory name redacts to a placeholder whose count is already
    reported, and a save filename redacts to a constant, so emitting either by
    default would spend injected context on a string carrying no information.
    Asserting the KEYS are absent is stronger than asserting their values are
    clean: a redacted-but-present field would pass a value sweep and still be
    the shape change this pins.
    """
    payload = probe_payload()

    assert "account_dirs" not in payload["save"]
    assert "newest_name" not in payload["save"]
    # Non-vacuity: the keys are absent because they were WITHHELD, not because
    # the probe found nothing to report about.
    account_count = len(machine.account_dirs)
    assert payload["save"]["accounts"] == account_count
    assert payload["save"]["savs"] == 1


def test_default_printed_line_carries_no_account_id_world_name_or_home_path(
    machine: FakeMachine, capsys: pytest.CaptureFixture[str]
) -> None:
    """The rendered line is swept as a STRING, not only as parsed fields.

    This is the form the SessionStart hook actually injects. A value can be
    absent from every field a test thought to check and still be sitting in the
    line - in a resolver label, in a key nobody enumerated, in a diagnostic.
    """
    code, line = run_main(capsys)

    assert code == 0
    assert_absent(line, machine)
    assert json.loads(line)["redacted"] is True


# ---------------------------------------------------------------------------
# The negative half - the opt-in has to actually opt in
# ---------------------------------------------------------------------------


def test_unredacted_payload_emits_the_account_ids_the_world_name_and_the_home_path(
    machine: FakeMachine,
) -> None:
    """The counterpart to the default-path tests, and not optional.

    An opt-in that emits nothing is as much a defect as a default that leaks,
    and every "absent" assertion in this file would pass against a probe whose
    output was empty. Requiring the same planted values to be PRESENT here is
    what makes the absent assertions mean "redacted" rather than "missing".
    """
    payload = probe_payload(unredacted=True)
    rendered = json.dumps(payload)

    assert payload["redacted"] is False
    assert sorted(payload["save"]["account_dirs"]) == sorted(FAKE_ACCOUNT_IDS)
    assert payload["save"]["newest_name"] == FAKE_SAVE_FILENAME
    assert_present(payload["save"]["root_path"], "save root", machine.save_root.as_posix())
    assert_present(payload["game"]["dir"], "install path", machine.game_dir.as_posix())

    for label, value in personal_values(machine).items():
        if label == "home path (native)":
            # The probe renders paths as posix, so the native spelling is the
            # one form that is legitimately absent from an unredacted payload.
            continue
        assert_present(rendered, label, value)


def test_unredacted_printed_line_emits_what_the_default_line_withholds(
    machine: FakeMachine, capsys: pytest.CaptureFixture[str]
) -> None:
    """Same pair, one level up: the string the flag actually produces."""
    code, line = run_main(capsys, "--unredacted")

    assert code == 0
    assert json.loads(line)["redacted"] is False
    assert_present(line, "world name", FAKE_WORLD_NAME)
    assert_present(line, "account id", NEWEST_FAKE_ACCOUNT_ID)
    assert_present(line, "home path", machine.home.as_posix())


def test_the_json_alias_does_not_lift_redaction(
    machine: FakeMachine, capsys: pytest.CaptureFixture[str]
) -> None:
    """--json is a seam-compatibility alias and must not be a second opt-in.

    The flag exists because callers pass it; the output was JSON either way. A
    flag that quietly widened what is emitted would be the worst kind of leak,
    because nothing about its name suggests it could.
    """
    code, line = run_main(capsys, "--json")

    assert code == 0
    assert_absent(line, machine)
    assert json.loads(line)["redacted"] is True


# ---------------------------------------------------------------------------
# Redaction is POSITIONAL, and it is not fixed for one platform
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "account_dir"), ACCOUNT_DIR_SHAPES, ids=[shape[0] for shape in ACCOUNT_DIR_SHAPES]
)
def test_default_output_redacts_an_account_segment_sitting_mid_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, label: str, account_dir: str
) -> None:
    """Whatever occupies the account-id position is personal data, mid-path too.

    CLOCKSPEED_SAVE_ROOT accepts any directory, so an operator who keeps a
    backup folder inside their own account directory hands the probe a path
    whose account segment is in the MIDDLE with a tail after it. Two failures
    are ruled out at once. A prefix-only redactor would strip the home and
    leave the account segment standing further along the string. A redactor
    keyed on seventeen digits - which one earlier fix in this project was -
    passes the last case here and leaks the other two, which is why the shapes
    deliberately share no character class.

    The tail is asserted to SURVIVE. A redactor that truncated everything after
    the marker would satisfy the negative assertion while destroying the shape
    the field exists to communicate.
    """
    local = tmp_path / FAKE_HOME_DIR_NAME / "AppData" / "Local"
    relocated = local.joinpath(*locate.SAVE_ROOT_PARTS) / account_dir / "Backup"
    relocated.mkdir(parents=True)
    monkeypatch.setenv(locate.ENV_SAVE_ROOT, str(relocated))

    payload = probe_payload()
    root_path = payload["save"]["root_path"]

    leaked = account_dir.lower() in json.dumps(payload).lower()
    assert not leaked, f"the default output left a {label} account directory standing"

    # Bools before the asserts: on failure root_path holds the very path this
    # test exists to keep out of the report.
    tokenised = locate.ACCOUNT_DIR_PLACEHOLDER in root_path
    structural = "/".join(locate.SAVE_ROOT_PARTS) in root_path
    tail_survived = root_path.endswith("/Backup")
    assert tokenised, f"a {label} account segment vanished without leaving a placeholder"
    assert structural, "the save-root marker did not survive redaction"
    assert tail_survived, (
        "the account segment went, but so did the tail after it - a negative assertion "
        "alone rules out without pinning down (CONVENTIONS.md section 7.2)"
    )


# ---------------------------------------------------------------------------
# The git facts - CS-206
# ---------------------------------------------------------------------------


def git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run git in ``cwd`` and return the completed process."""
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        check=False,
    )


class Checkout(NamedTuple):
    """A real throwaway repository, held behind a withholding repr.

    THE REPR IS NOT DECORATION, and it was added because the failure report
    proved it necessary: pytest prints every fixture value it can reach at the
    top of a failure, and returning a bare Path put the operator's real account
    name into the report on the very run that exists to prove it must not be
    printed (CLAUDE.md non-negotiable 12 - exception context is an echo path).
    tmp_path lives under the real profile directory, so the synthetic tree
    built inside it does too. FakeMachine above withholds its paths for exactly
    this reason; this is the same guard for the same reason.
    """

    root: Path
    home: Path

    def __repr__(self) -> str:
        """Render without any path."""
        return "<Checkout under the synthetic home, paths withheld>"


@pytest.fixture
def checkout_under_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Checkout:
    """A real git repository under the synthetic home, with the probe aimed at it.

    THE REPOSITORY IS REAL, and that is the point. The defect being pinned is
    what _git_facts() does with the string git hands back, so the string comes
    from git. A monkeypatched _git() would have proven only that this file and
    the probe agree about what git returns.

    GIT_CONFIG_GLOBAL and GIT_CONFIG_SYSTEM are aimed at files that do not
    exist, so the operator's own git configuration cannot answer. Without that,
    a machine with core.hooksPath set globally would report a hooks path in the
    test that asserts an unconfigured one reads as null, and the test would be
    grading the machine rather than the code.

    sys.path is REPLACED WITH A COPY rather than left alone. Pointing
    repo_root() at tmp_path makes _load_locate() and _build_string() insert
    directories under it, and monkeypatch restores the attribute afterwards,
    where an in-place insert would outlive the test and leave a deleted
    directory on the import path for everything that ran after it.

    Returns:
        The checkout, whose ``root`` is also what facts_probe.repo_root() now
        returns.
    """
    home = tmp_path / FAKE_HOME_DIR_NAME
    root = home / SYNTHETIC_CHECKOUT_DIR_NAME
    root.mkdir(parents=True)

    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "absent" / "gitconfig-global"))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(tmp_path / "absent" / "gitconfig-system"))

    initialised = git("init", "-q", "-b", SYNTHETIC_BRANCH, cwd=root).returncode == 0
    assert initialised, "the throwaway repository could not be initialised"

    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(facts_probe, "repo_root", lambda: root)
    return Checkout(root=root, home=home)


def set_hooks_path(checkout: Checkout, value: str) -> None:
    """Set core.hooksPath in the throwaway repository, and prove it took.

    Every result is reduced to a bool before it is asserted on. A
    CompletedProcess reprs its own argument list, and that list holds the
    absolute path this whole section exists to keep out of a failure report.
    """
    written = git("config", "core.hooksPath", value, cwd=checkout.root).returncode == 0
    assert written, "core.hooksPath could not be written in the throwaway repository"
    readback = git("config", "--get", "core.hooksPath", cwd=checkout.root)
    # Setting a value is not evidence the value took - scripts/install_hooks.py
    # reads its own write back for the same reason.
    took = readback.returncode == 0 and readback.stdout.strip() == value.strip()
    assert took, "core.hooksPath did not take in the throwaway repository"


def slash_normalised(rendered: str) -> str:
    r"""Collapse raw and JSON-escaped backslashes so one needle finds both forms.

    json.dumps() renders a Windows path's separators as ``\\``, so a needle
    spelled with single backslashes finds nothing in the serialised payload and
    a posix needle finds nothing in the raw one. A sweep that missed for that
    reason would report clean on exactly the unredacted output it exists to
    catch.
    """
    return rendered.replace("\\\\", "/").replace("\\", "/")


def assert_no_home_segment(rendered: str, checkout: Checkout) -> None:
    """Assert no rendering of the synthetic home survived into ``rendered``.

    FAKE_HOME_DIR_NAME is the load-bearing needle: it is a segment of every
    spelling of the home path - native, posix, escaped - so its absence rules
    out all of them at once. The full paths are swept as well so a failure can
    say which form leaked. Labels only in the message; the paths themselves
    contain the operator's real temporary directory and stay out of the report.
    """
    normalised = slash_normalised(rendered).lower()
    candidates = {
        "synthetic home directory name": FAKE_HOME_DIR_NAME,
        "synthetic home path": checkout.home.as_posix(),
        "synthetic checkout path": checkout.root.as_posix(),
    }
    leaked = sorted(label for label, value in candidates.items() if value.lower() in normalised)
    assert not leaked, f"the default git facts leaked: {', '.join(leaked)}"


def test_default_hooks_path_inside_the_checkout_carries_no_home_path(
    checkout_under_home: Checkout,
) -> None:
    """CS-206: an absolute hooks path under a home directory must not be emitted.

    This is the acceptance criterion. The checkout sits under the synthetic
    home and core.hooksPath holds the ABSOLUTE path to its .githooks - which is
    the shape this machine's own checkout carries, measured rather than
    assumed - so the raw value contains the home directory in full.

    The positive half is asserted in the same breath. A field that had been
    emptied, nulled or replaced by a bare token would satisfy the absence
    assertion while telling a SessionStart reader nothing about whether the
    hooks are wired, and "are the hooks wired, and to this repository's own
    .githooks" is the only question the field answers.
    """
    hooks_dir = checkout_under_home.root / HOOKS_DIR_NAME
    hooks_dir.mkdir()
    set_hooks_path(checkout_under_home, str(hooks_dir))

    payload = probe_payload()

    assert_no_home_segment(json.dumps(payload), checkout_under_home)
    assert payload["git"]["hooks_path"] == HOOKS_DIR_NAME


def test_default_hooks_path_outside_the_checkout_is_redacted_but_still_readable(
    checkout_under_home: Checkout,
) -> None:
    """A hooks path that is NOT inside the checkout has to survive on redaction.

    Nothing requires core.hooksPath to point inside the work tree, so the
    repo-relative rendering cannot be the only answer. Here the directory sits
    beside the checkout under the synthetic home, where relativising is
    impossible and locate.redact() is the whole defence.

    The tail is asserted to SURVIVE, for the reason the account-segment test
    above gives: a renderer that truncated everything after the home token
    would satisfy the negative assertion while destroying the shape the field
    exists to communicate.
    """
    shared_hooks = checkout_under_home.home / SHARED_HOOKS_DIR_NAME
    shared_hooks.mkdir()
    set_hooks_path(checkout_under_home, str(shared_hooks))

    payload = probe_payload()
    emitted = payload["git"]["hooks_path"]

    assert_no_home_segment(json.dumps(payload), checkout_under_home)
    # Bools before the asserts: on failure `emitted` holds the very path these
    # assertions exist to keep out of the report.
    tokenised = HOME_PLACEHOLDER in emitted
    tail_survived = emitted.endswith("/" + SHARED_HOOKS_DIR_NAME)
    assert tokenised, "the home directory vanished without leaving a placeholder"
    assert tail_survived, "the home went, but so did the hooks directory name after it"


def test_default_branch_does_not_carry_an_account_name_shaped_segment(
    checkout_under_home: Checkout,
) -> None:
    """A branch name is operator-chosen free text and reaches the payload verbatim.

    "<user>/wip" is an everyday branch convention, and the Windows account name
    is personal data (CLAUDE.md non-negotiable 3) in the same rank as a home
    path. The branch is not a path and can never be one - git's ref format
    forbids the backslash, the colon and the space - so this is a distinct leak
    shape from the hooks path, found by sweeping the whole payload rather than
    the one field CS-206 named.
    """
    payload = probe_payload()

    assert_no_home_segment(json.dumps(payload), checkout_under_home)
    assert payload["git"]["branch"] == REDACTED_BRANCH


def test_the_printed_default_line_carries_no_home_segment_from_the_git_facts(
    checkout_under_home: Checkout, capsys: pytest.CaptureFixture[str]
) -> None:
    """The swept form is the one the SessionStart hook actually injects.

    The payload tests above read parsed fields. A value can be absent from
    every field a test thought to check and still sit in the printed line, so
    the line is swept as a string with both git facts planted at once.
    """
    hooks_dir = checkout_under_home.root / HOOKS_DIR_NAME
    hooks_dir.mkdir()
    set_hooks_path(checkout_under_home, str(hooks_dir))

    code, line = run_main(capsys)

    assert code == 0
    assert_no_home_segment(line, checkout_under_home)
    assert json.loads(line)["redacted"] is True


def test_an_unconfigured_hooks_path_reads_as_null_and_not_as_configured(
    checkout_under_home: Checkout,
) -> None:
    """Not configured must not become something that reads as configured.

    A GUARD ON THE FIX, not a demonstration of the defect - it passed before
    CS-206 and has to keep passing after. It is here because the obvious way to
    write the fix breaks it: locate.redact() takes an ``object`` and
    stringifies it, so ``redact(hooks_path) or None`` turns the None that means
    "core.hooksPath is unset" into the truthy string "None", and an
    unprotected checkout would then report a wired one.
    """
    unset = git("config", "--get", "core.hooksPath", cwd=checkout_under_home.root).returncode != 0
    assert unset, "the throwaway repository unexpectedly has a hooks path"

    payload = probe_payload()

    assert payload["git"]["hooks_path"] is None
    # Non-vacuity: the field is null because nothing is configured, not because
    # the git facts failed to be collected at all.
    assert payload["git"]["branch"] == REDACTED_BRANCH


def test_an_empty_hooks_path_reads_as_null_and_not_as_configured(
    checkout_under_home: Checkout,
) -> None:
    """An empty value is a DIFFERENT state from an unset one, and both mean unwired.

    Measured rather than assumed: with core.hooksPath set to the empty string,
    `git config --get core.hooksPath` exits 0 and prints a bare newline, so
    _git() returns "" where an unset key makes it return None. Two inputs, one
    correct answer - an empty hooks path wires nothing, so reporting it as
    configured would be the same lie as reporting an unset one.
    """
    written = git("config", "core.hooksPath", "", cwd=checkout_under_home.root).returncode == 0
    assert written
    configured = git("config", "--get", "core.hooksPath", cwd=checkout_under_home.root)
    reads_back_empty = configured.returncode == 0 and configured.stdout.strip() == ""
    assert reads_back_empty, "an empty core.hooksPath no longer reads back as an empty string"

    payload = probe_payload()

    assert payload["git"]["hooks_path"] is None


def test_the_relative_hooks_path_the_installer_writes_survives_unchanged(
    checkout_under_home: Checkout,
) -> None:
    """scripts/install_hooks.py writes ".githooks", and that must render as itself.

    A second guard on the fix rather than a demonstration of the defect. The
    installer sets the RELATIVE value (scripts/install_hooks.py: it writes
    HOOKS_DIR_NAME, not an absolute path), so the overwhelmingly common input
    to this field carries no personal data at all, and a renderer that
    tokenised or relativised it into something else would degrade the normal
    case in order to fix the rare one.
    """
    set_hooks_path(checkout_under_home, HOOKS_DIR_NAME)

    payload = probe_payload()

    assert payload["git"]["hooks_path"] == HOOKS_DIR_NAME


def test_unredacted_git_facts_emit_the_raw_branch_and_the_raw_hooks_path(
    checkout_under_home: Checkout,
) -> None:
    """The negative half, without which every absence assertion above is vacuous.

    A probe that emitted null for both fields would satisfy all of them. This
    requires the same planted values to be PRESENT under --unredacted, so the
    pair pins "redacted by default" rather than "the git facts are missing",
    and it keeps the ``redacted: false`` flag honest - a payload that claimed
    to be unredacted while still reducing two fields would be over-claiming.
    """
    hooks_dir = checkout_under_home.root / HOOKS_DIR_NAME
    hooks_dir.mkdir()
    set_hooks_path(checkout_under_home, str(hooks_dir))

    payload = probe_payload(unredacted=True)
    rendered = slash_normalised(json.dumps(payload))

    assert payload["redacted"] is False
    assert payload["git"]["branch"] == SYNTHETIC_BRANCH
    assert_present(rendered, "hooks path", hooks_dir.as_posix())
    assert_present(rendered, "home directory", checkout_under_home.home.as_posix())


def break_the_data_layer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make _load_locate() fail, which is the only way locate.redact() is absent."""

    def unavailable() -> Any:
        message = "synthetic: the data layer is not importable"
        raise ImportError(message)

    monkeypatch.setattr(facts_probe, "_load_locate", unavailable)


def test_git_facts_are_withheld_rather_than_leaked_when_the_redactor_is_missing(
    checkout_under_home: Checkout, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A GUARD ON A NON-DEFAULT PATH, which is exactly where guards go untested.

    "Delete the guard; if the suite stays green, the guard was never exercised"
    (CONVENTIONS.md section 7.2). The probe tolerates clockspeed.data.locate
    failing to import - it reports probe_error and carries on - and on that path
    there is no redactor to hand the git facts to. The tempting answer is to
    emit them raw, which would mean the probe leaks precisely when its own
    privacy machinery is broken. It withholds instead, and this is the only
    test that ever reaches that branch.
    """
    shared_hooks = checkout_under_home.home / SHARED_HOOKS_DIR_NAME
    shared_hooks.mkdir()
    set_hooks_path(checkout_under_home, str(shared_hooks))
    break_the_data_layer(monkeypatch)

    payload = probe_payload()

    assert payload["probe_error"] == "clockspeed.data.locate not importable"
    assert_no_home_segment(json.dumps(payload), checkout_under_home)
    # WITHHELD, not None. A reader has to be able to tell a wired checkout whose
    # value is being suppressed from one with no hooks configured at all - a
    # fresh clone runs zero protection until someone wires it, so reporting an
    # unwired repository as wired, or the reverse, is the whole risk here.
    assert payload["git"]["hooks_path"] == WITHHELD_PLACEHOLDER
    assert payload["git"]["branch"] == WITHHELD_PLACEHOLDER


def test_a_hooks_path_inside_the_checkout_relativises_without_needing_the_redactor(
    checkout_under_home: Checkout, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The repo-relative rendering is structural, so it survives a broken data layer.

    This is the other half of the guard above, and it is why the probe
    relativises FIRST and redacts second: the common case - the installer's own
    wiring, pointing at the repository's own .githooks - needs no redactor at
    all, so the most useful answer is also the one least able to leak.
    """
    hooks_dir = checkout_under_home.root / HOOKS_DIR_NAME
    hooks_dir.mkdir()
    set_hooks_path(checkout_under_home, str(hooks_dir))
    break_the_data_layer(monkeypatch)

    payload = probe_payload()

    assert payload["probe_error"] == "clockspeed.data.locate not importable"
    assert_no_home_segment(json.dumps(payload), checkout_under_home)
    assert payload["git"]["hooks_path"] == HOOKS_DIR_NAME


# ---------------------------------------------------------------------------
# Read-only, and answerable on a machine that has never had the game
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("unredacted", [False, True], ids=["default", "unredacted"])
def test_probing_writes_nothing_into_the_save_tree_or_the_install(
    machine: FakeMachine, unredacted: bool
) -> None:
    """CLAUDE.md non-negotiable 1: never write to the install or the save directory.

    The probe walks the save root with rglob and stats what it finds, and this
    proves the walk stayed a read. A created, deleted, truncated or rewritten
    entry moves the snapshot, and so does any write into a directory, because
    adding or removing a child moves that directory's own mtime.
    """
    saves_before = tree_snapshot(machine.save_root)
    install_before = tree_snapshot(machine.game_dir)

    probe_payload(unredacted=unredacted)

    saves_after = tree_snapshot(machine.save_root)
    install_after = tree_snapshot(machine.game_dir)
    saves_unchanged = saves_after == saves_before
    install_unchanged = install_after == install_before
    assert saves_unchanged, "the probe changed the save tree"
    assert install_unchanged, "the probe changed the install tree"


def test_probe_answers_without_an_install_a_save_root_or_localappdata(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CI case: ubuntu, no game, no save directory, no LOCALAPPDATA.

    Absent content is reported and never fatal (CLAUDE.md non-negotiable 7).
    The autouse fixture already aims every override at a path that does not
    exist; this removes LOCALAPPDATA as well so nothing at all can resolve, and
    pins the exit code because that is what a hook reads.
    """
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    code, line = run_main(capsys)
    payload = json.loads(line)

    assert code == 0
    assert payload["schema"] == EXPECTED_SCHEMA
    assert payload["redacted"] is True
    assert payload["game"]["found"] is False
    assert payload["save"]["root"] is False
    assert payload["save"]["accounts"] == 0
    assert payload["save"]["savs"] == 0
    assert payload["save"]["newest"] is None
    assert payload["save"]["root_path"] is None
    assert "probe_error" not in payload


def test_schema_2_reports_a_redacted_path_on_the_default_path(machine: FakeMachine) -> None:
    """The schema-2 shape change, pinned so a silent revert is visible.

    Schema 1 emitted "dir" and "root_path" only under --unredacted; schema 2
    carries a REDACTED rendering of both on the default path. A revert to the
    old shape with the version left alone is exactly the drift the field exists
    to make visible, and nothing but a test can see it happen.
    """
    payload = probe_payload()

    assert payload["schema"] == EXPECTED_SCHEMA
    assert isinstance(payload["save"]["root_path"], str)
    assert isinstance(payload["game"]["dir"], str)
    assert_not_the_raw_path(payload["save"]["root_path"], machine.save_root, "save.root_path")
    assert_not_the_raw_path(payload["game"]["dir"], machine.game_dir, "game.dir")
