"""Tests for clockspeed.data.locate - install, save root and account discovery.

Every test here runs on a machine with NO game installed and NO save
directory. That is the CS-200 acceptance criterion rather than a convenience:
the rule suite has to be green on a clean checkout that has never seen the
game. Nothing below reads the real install, the real save root or the real
config/local.json. An autouse fixture clears all three resolver environment
variables and points the config-path override at tmp_path, because a resolver
that ignored an override would otherwise be answered correctly by the
operator's own machine and the test would pass while proving nothing.

PRIVACY (BOOTSTRAP.md section 2.2, CLAUDE.md non-negotiable 3): the account
directory name is a platform account id and is personal data. No real account
id, no real home path and no real machine name appears in this file. The
account-id-shaped strings below are synthetic literals invented for the
fixtures. The privacy assertions record their result as a bool BEFORE
asserting, so a failure message can never print the very string the test
exists to keep out of the output - and they assert on the returned string
rather than through a spy that raises, because a raising spy is vacuous under
fail-soft code (CONVENTIONS.md section 7.2).

WHY THE REDACTION TESTS TAKE FIVE SHAPES AND NOT ONE. A redactor written
against ONE shape of account directory is a redactor that has been tested
against its own assumption. Steam names the directory with digits; Epic uses a
hex token, the Microsoft Store uses a braceless GUID, and the documented
CLOCKSPEED_ACCOUNT_DIR override accepts any name at all. Only the POSITION is
invariant, so the shapes below deliberately share no character class. The
fifth shape is the operating system's own 8.3 short rendering of the home
directory, which no environment variable spells the same way and which
therefore has to come from the operating system rather than from the module
under test.
"""

from __future__ import annotations

import errno
import json
import os
import tempfile
from pathlib import Path

import pytest

from clockspeed.data import locate

# ---------------------------------------------------------------------------
# Synthetic fixture material
# ---------------------------------------------------------------------------

# Account-id shaped, 17 digits like a platform id, and invented here. These are
# not anybody's account ids; they exist so the ordering and redaction rules can
# be exercised without a real one ever entering the repository.
NEWEST_FAKE_ACCOUNT_ID = "10000000000000001"
MIDDLE_FAKE_ACCOUNT_ID = "20000000000000002"
OLDEST_FAKE_ACCOUNT_ID = "30000000000000003"

# The four account-directory shapes a save root can actually hold, all four
# invented here and none resembling any real platform's prefix. They share no
# character class on purpose: an all-digit rule matches only the last one, and
# that is exactly how a redactor comes to be "fixed" for one shape.
ACCOUNT_DIR_SHAPES: tuple[tuple[str, str], ...] = (
    ("hex-token", "a1b2c3d4e5f60718293a4b5c6d7e8f90"),
    ("digits-with-a-letter", "1000000000000001a"),
    ("braceless-guid", "2f9a1c4e-0b77-4d2a-9c31-8ee5f0a1b2c3"),
    ("seventeen-digit", NEWEST_FAKE_ACCOUNT_ID),
)

# A world name is operator-chosen and is personal data (CLAUDE.md rule 3). A
# save file is named after it, so the filename carries it into every path.
FAKE_WORLD_NAME = "SyntheticWorldNameForTests"

# A fixed epoch so directory ages are set explicitly rather than inherited from
# whatever order the filesystem happened to create them in.
_BASE_MTIME = 1_700_000_000.0
_ONE_HOUR = 3600.0


def _make_save_root(tmp_path: Path) -> Path:
    """Build an empty save root of the real shape under tmp_path."""
    root = tmp_path.joinpath("local", *locate.SAVE_ROOT_PARTS)
    root.mkdir(parents=True)
    return root


def _make_account_dir(save_root: Path, name: str, age_rank: int = 0) -> Path:
    """Create an account directory. age_rank 0 is the most recently modified."""
    path = save_root / name
    path.mkdir()
    stamp = _BASE_MTIME - (age_rank * _ONE_HOUR)
    os.utime(path, (stamp, stamp))
    return path


def _write_local_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, payload: object) -> Path:
    """Write a config/local.json stand-in and point the module at it."""
    path = tmp_path / "local.json"
    text = payload if isinstance(payload, str) else json.dumps(payload)
    path.write_text(text, encoding="utf-8")
    monkeypatch.setenv(locate.ENV_LOCAL_CONFIG, str(path))
    return path


@pytest.fixture(autouse=True)
def _isolated_resolution(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Detach every test from the operator's machine and their local config.

    Without this, a resolver that silently ignored an override would still
    return the right-looking answer on a developer machine that has the game
    installed, and the override tests would be green about nothing.

    The account-directory memory is replaced with a fresh empty list too. The
    resolver remembers the names it hands out so redact() can strip an
    override that points outside the save root, and that memory is module
    state: left alone, one test's synthetic account name would still be a
    redaction needle in the next test, and a later assertion could pass
    because of a neighbour rather than because of the code. Replacing the
    ATTRIBUTE through monkeypatch also restores it automatically, which
    calling a reset helper would not.

    The remembered SAVE ROOTS are reset for the same reason and are the newer
    half of the same hazard (CS-454). A save root this module resolved becomes
    a redaction ANCHOR, so a neighbouring test's synthetic root would keep
    rewriting the segment below it here, and a leak assertion could pass
    because of that neighbour rather than because of the code.
    """
    for name in (locate.ENV_GAME_DIR, locate.ENV_SAVE_ROOT, locate.ENV_ACCOUNT_DIR):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(locate.ENV_LOCAL_CONFIG, str(tmp_path / "absent" / "local.json"))
    monkeypatch.setattr(locate, "_RESOLVED_ACCOUNT_NAMES", [])
    monkeypatch.setattr(locate, "_RESOLVED_SAVE_ROOTS", [])


def account_name_renderings() -> set[str]:
    """Every rendering of this machine's account name, read from the system.

    THE ORACLE MUST NOT BE THE CODE UNDER TEST. ``redact(x) != x`` looks like
    a test for "x held personal data" and is not one - it reports whatever the
    redactor happens to recognise, so a redactor with a blind spot grades
    itself clean on exactly the strings it cannot see (CONVENTIONS.md section
    15.1). Everything here is therefore derived from the operating system and
    the environment directly, with nothing from clockspeed.data.locate.

    Two renderings exist on Windows and they are not substrings of each other.
    The long one is the account name as the profile directory spells it. The
    short one is the 8.3 form, six characters plus a tilde and a digit, which
    is what tempfile.gettempdir() hands back on a default install - the
    rendering that defeated the first version of the redactor.

    Returns:
        The distinct non-empty renderings. Positions are read from the profile
        directory's own depth rather than from a hardcoded index, so the
        derivation does not assume a particular directory layout.
    """
    found = {os.environ.get("USERNAME") or "", os.environ.get("USER") or ""}
    try:
        home = Path.home()
    except (OSError, RuntimeError):
        return {name for name in found if name}
    found.add(home.name)
    depth = len(home.parts)
    temporary = Path(tempfile.gettempdir()).parts
    if len(temporary) >= depth and temporary[: depth - 1] == home.parts[: depth - 1]:
        found.add(temporary[depth - 1])
    return {name for name in found if name}


# ---------------------------------------------------------------------------
# Install resolution and its override precedence
# ---------------------------------------------------------------------------


def test_game_dir_environment_override_beats_config_and_detection(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from_env = tmp_path / "install-from-env"
    from_config = tmp_path / "install-from-config"
    from_env.mkdir()
    from_config.mkdir()
    _write_local_config(monkeypatch, tmp_path, {locate.CONFIG_GAME_DIR: str(from_config)})
    monkeypatch.setenv(locate.ENV_GAME_DIR, str(from_env))

    resolved, source = locate.resolve_game_dir()

    assert resolved == from_env
    assert source == f"env:{locate.ENV_GAME_DIR}"


def test_game_dir_config_override_beats_detection(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from_config = tmp_path / "install-from-config"
    from_config.mkdir()
    _write_local_config(monkeypatch, tmp_path, {locate.CONFIG_GAME_DIR: str(from_config)})

    resolved, source = locate.resolve_game_dir()

    assert resolved == from_config
    assert source == f"config:{locate.CONFIG_GAME_DIR}"


def test_game_dir_environment_override_that_is_not_a_directory_is_reported_not_raised(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(locate.ENV_GAME_DIR, str(tmp_path / "no-such-install"))

    resolved, source = locate.resolve_game_dir()

    assert resolved is None
    assert locate.ENV_GAME_DIR in source
    assert "not a directory" in source


def test_game_dir_config_override_that_is_not_a_directory_is_reported_not_raised(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write_local_config(
        monkeypatch, tmp_path, {locate.CONFIG_GAME_DIR: str(tmp_path / "no-such-install")}
    )

    resolved, source = locate.resolve_game_dir()

    assert resolved is None
    assert locate.CONFIG_GAME_DIR in source
    assert "not a directory" in source


def test_missing_game_install_resolves_to_none_without_raising(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Detection is aimed at an empty tmp_path so this is deterministic on a
    # machine that DOES have the game installed. Unknown content is flagged and
    # skipped, never fatal (CLAUDE.md non-negotiable 7).
    monkeypatch.setattr(locate, "_steam_library_paths", list)
    monkeypatch.setattr(locate, "_drive_roots", lambda: [tmp_path])

    resolved, source = locate.resolve_game_dir()

    assert resolved is None
    assert source == "unresolved"


# ---------------------------------------------------------------------------
# Save root resolution and its override precedence
# ---------------------------------------------------------------------------


def test_save_root_environment_override_beats_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from_env = _make_save_root(tmp_path)
    from_config = tmp_path / "other-save-root"
    from_config.mkdir()
    _write_local_config(monkeypatch, tmp_path, {locate.CONFIG_SAVE_ROOT: str(from_config)})
    monkeypatch.setenv(locate.ENV_SAVE_ROOT, str(from_env))

    assert locate.resolve_save_root() == from_env


def test_save_root_config_override_is_used_when_the_environment_is_unset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from_config = _make_save_root(tmp_path)
    _write_local_config(monkeypatch, tmp_path, {locate.CONFIG_SAVE_ROOT: str(from_config)})

    assert locate.resolve_save_root() == from_config


def test_save_root_falls_back_to_localappdata_when_no_override_is_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    detected = _make_save_root(tmp_path)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))

    assert locate.resolve_save_root() == detected


def test_missing_save_root_resolves_to_none_without_raising(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "empty-local"))

    assert locate.resolve_save_root() is None


def test_save_root_override_that_is_not_a_directory_resolves_to_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(locate.ENV_SAVE_ROOT, str(tmp_path / "no-such-save-root"))

    assert locate.resolve_save_root() is None


# ---------------------------------------------------------------------------
# Account directories
# ---------------------------------------------------------------------------


def test_account_dirs_are_ordered_most_recently_modified_first(tmp_path: Path) -> None:
    save_root = _make_save_root(tmp_path)
    # Created oldest-first so the answer cannot come from creation order.
    oldest = _make_account_dir(save_root, OLDEST_FAKE_ACCOUNT_ID, age_rank=2)
    middle = _make_account_dir(save_root, MIDDLE_FAKE_ACCOUNT_ID, age_rank=1)
    newest = _make_account_dir(save_root, NEWEST_FAKE_ACCOUNT_ID, age_rank=0)

    assert locate.numeric_account_dirs(save_root) == [newest, middle, oldest]


def test_account_dirs_ignores_non_numeric_names_and_files(tmp_path: Path) -> None:
    save_root = _make_save_root(tmp_path)
    numeric = _make_account_dir(save_root, NEWEST_FAKE_ACCOUNT_ID)
    (save_root / "common").mkdir()
    (save_root / "12345678901234567.txt").write_text("not a directory", encoding="utf-8")

    assert locate.numeric_account_dirs(save_root) == [numeric]


def test_account_dirs_is_empty_when_there_is_no_save_root(tmp_path: Path) -> None:
    assert locate.numeric_account_dirs(None) == []
    assert locate.numeric_account_dirs(tmp_path / "no-such-save-root") == []


def test_account_dir_defaults_to_the_most_recently_modified(tmp_path: Path) -> None:
    save_root = _make_save_root(tmp_path)
    _make_account_dir(save_root, OLDEST_FAKE_ACCOUNT_ID, age_rank=1)
    newest = _make_account_dir(save_root, NEWEST_FAKE_ACCOUNT_ID, age_rank=0)

    assert locate.resolve_account_dir(save_root) == newest


def test_account_dir_environment_override_beats_most_recently_modified(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    save_root = _make_save_root(tmp_path)
    chosen = _make_account_dir(save_root, OLDEST_FAKE_ACCOUNT_ID, age_rank=1)
    _make_account_dir(save_root, NEWEST_FAKE_ACCOUNT_ID, age_rank=0)
    monkeypatch.setenv(locate.ENV_ACCOUNT_DIR, OLDEST_FAKE_ACCOUNT_ID)

    assert locate.resolve_account_dir(save_root) == chosen


def test_account_dir_config_override_beats_detection_and_loses_to_the_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    save_root = _make_save_root(tmp_path)
    from_config = _make_account_dir(save_root, MIDDLE_FAKE_ACCOUNT_ID, age_rank=1)
    from_env = _make_account_dir(save_root, OLDEST_FAKE_ACCOUNT_ID, age_rank=2)
    _make_account_dir(save_root, NEWEST_FAKE_ACCOUNT_ID, age_rank=0)
    _write_local_config(monkeypatch, tmp_path, {locate.CONFIG_ACCOUNT_DIR: MIDDLE_FAKE_ACCOUNT_ID})

    assert locate.resolve_account_dir(save_root) == from_config

    monkeypatch.setenv(locate.ENV_ACCOUNT_DIR, OLDEST_FAKE_ACCOUNT_ID)

    assert locate.resolve_account_dir(save_root) == from_env


def test_account_dir_override_may_be_an_absolute_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    save_root = _make_save_root(tmp_path)
    _make_account_dir(save_root, NEWEST_FAKE_ACCOUNT_ID)
    elsewhere = tmp_path / "relocated-account-dir"
    elsewhere.mkdir()
    monkeypatch.setenv(locate.ENV_ACCOUNT_DIR, str(elsewhere))

    assert locate.resolve_account_dir(save_root) == elsewhere


def test_account_dir_override_naming_a_missing_directory_resolves_to_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    save_root = _make_save_root(tmp_path)
    _make_account_dir(save_root, NEWEST_FAKE_ACCOUNT_ID)
    monkeypatch.setenv(locate.ENV_ACCOUNT_DIR, MIDDLE_FAKE_ACCOUNT_ID)

    assert locate.resolve_account_dir(save_root) is None


def test_account_dir_is_none_when_there_is_no_save_root() -> None:
    assert locate.resolve_account_dir(None) is None


# ---------------------------------------------------------------------------
# config/local.json
# ---------------------------------------------------------------------------


def test_absent_local_config_is_normal_and_not_an_error() -> None:
    # The autouse fixture already points the override at a path that does not
    # exist, which is the state on every machine that never wrote one.
    assert locate.local_config() == {}
    assert locate.resolve_game_dir()[1] != ""
    assert locate.resolve_account_dir(None) is None


def test_malformed_local_config_is_not_an_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write_local_config(monkeypatch, tmp_path, "{ this is not json")

    assert locate.local_config() == {}


def test_local_config_that_is_not_an_object_is_not_an_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write_local_config(monkeypatch, tmp_path, ["not", "an", "object"])

    assert locate.local_config() == {}


def test_local_config_default_path_is_the_tracked_config_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(locate.ENV_LOCAL_CONFIG, raising=False)

    path = locate.local_config_path()

    assert path.name == "local.json"
    assert path.parent.name == "config"


# ---------------------------------------------------------------------------
# config/local.json - a discarded declaration is REPORTED, not swallowed (CS-443)
# ---------------------------------------------------------------------------
#
# THE OPERATOR-FACING DEFECT. Every branch below used to return {} without a
# word, so a local config the operator had genuinely written was discarded and
# the tool then advised them to write the very declaration they had already
# written. "Never raises" is a promise about control flow; it was being read as
# a licence to lose configuration in silence, which is a different thing.
#
# ABSENCE IS NOT ONE OF THESE CASES and must stay silent. Every machine is
# expected to have no config/local.json - it is gitignored and the normal state
# is not to have one. A warning on absence would fire on every clean checkout
# and train the operator to ignore the channel, which is how a real report gets
# missed. The distinction between "absent" and "present and discarded" is the
# whole item.


def _collect(
    payload: object, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[dict[str, str], list[locate.LocalConfigWarning]]:
    """Read a written-out local config, capturing whatever it reported."""
    _write_local_config(monkeypatch, tmp_path, payload)
    warnings: list[locate.LocalConfigWarning] = []
    return locate.local_config(warnings=warnings), warnings


def test_absent_local_config_reports_nothing_because_absence_is_normal() -> None:
    # The autouse fixture points the override at a path that does not exist.
    warnings: list[locate.LocalConfigWarning] = []

    assert locate.local_config(warnings=warnings) == {}
    assert warnings == []


def test_a_well_formed_local_config_reports_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    values, warnings = _collect({locate.CONFIG_GAME_DIR: str(tmp_path)}, monkeypatch, tmp_path)

    assert values == {locate.CONFIG_GAME_DIR: str(tmp_path)}
    assert warnings == []


def test_oversize_local_config_is_reported_rather_than_discarded_in_silence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    oversize = {locate.CONFIG_GAME_DIR: "x" * (locate.MAX_LOCAL_CONFIG_BYTES + 100)}

    values, warnings = _collect(oversize, monkeypatch, tmp_path)

    assert values == {}
    assert [item.code for item in warnings] == [locate.WARN_LOCAL_CONFIG_OVERSIZE]


def test_unreadable_local_config_is_reported_rather_than_discarded_in_silence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write_local_config(monkeypatch, tmp_path, {locate.CONFIG_GAME_DIR: str(tmp_path)})

    def unreadable(self: Path, *_args: object, **_kwargs: object) -> str:
        raise OSError(errno.EACCES, "Permission denied", str(self))

    monkeypatch.setattr(Path, "read_text", unreadable)
    warnings: list[locate.LocalConfigWarning] = []

    assert locate.local_config(warnings=warnings) == {}
    assert [item.code for item in warnings] == [locate.WARN_LOCAL_CONFIG_UNREADABLE]


def test_malformed_local_config_is_reported_rather_than_discarded_in_silence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    values, warnings = _collect("{ this is not json", monkeypatch, tmp_path)

    assert values == {}
    assert [item.code for item in warnings] == [locate.WARN_LOCAL_CONFIG_MALFORMED]


def test_non_mapping_local_config_is_reported_rather_than_discarded_in_silence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    values, warnings = _collect(["not", "an", "object"], monkeypatch, tmp_path)

    assert values == {}
    assert [item.code for item in warnings] == [locate.WARN_LOCAL_CONFIG_NOT_A_MAPPING]


def test_undecodable_local_config_is_reported_rather_than_raising(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Invalid UTF-8 must not escape as UnicodeDecodeError.

    read_text(encoding="utf-8") raises UnicodeDecodeError, which is a
    ValueError and NOT an OSError - so the OSError handler never saw it and it
    propagated out of a function whose docstring promises it never raises. The
    fix reports it; it does NOT pass errors="replace", because silently
    mangling an operator's declared path is the same defect class this item
    exists to remove.
    """
    path = tmp_path / "local.json"
    path.write_bytes(b'{"' + locate.CONFIG_GAME_DIR.encode() + b'": "\xff\xfe"}')
    monkeypatch.setenv(locate.ENV_LOCAL_CONFIG, str(path))
    warnings: list[locate.LocalConfigWarning] = []

    assert locate.local_config(warnings=warnings) == {}
    assert [item.code for item in warnings] == [locate.WARN_LOCAL_CONFIG_UNDECODABLE]


def test_a_non_string_value_is_reported_per_key_rather_than_dropped_in_silence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The quietest of the loss paths: the comprehension drops one key at a time.

    An operator who wrote a number, a list or a null where a path belongs got
    an empty mapping and no indication which key was at fault. The surviving
    string-valued keys must still be returned - one bad key is not a reason to
    discard the rest.
    """
    values, warnings = _collect(
        {locate.CONFIG_GAME_DIR: 17, locate.CONFIG_SAVE_ROOT: str(tmp_path)},
        monkeypatch,
        tmp_path,
    )

    assert values == {locate.CONFIG_SAVE_ROOT: str(tmp_path)}
    assert [item.code for item in warnings] == [locate.WARN_LOCAL_CONFIG_NON_STRING_VALUE]
    assert locate.CONFIG_GAME_DIR in warnings[0].subject


def test_every_discard_path_names_a_reason_without_echoing_the_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A skip record is an echo path (CLAUDE.md non-negotiable 12).

    The subject carries the config location, so it goes through redact() like
    every other path this module can put into a message. The oracle is derived
    from the operating system rather than from redact() itself, so a redactor
    with a blind spot cannot grade itself clean.
    """
    _, warnings = _collect("{ this is not json", monkeypatch, tmp_path)

    rendered = " ".join(f"{item.code} {item.subject} {item.detail}" for item in warnings)
    leaked = sum(1 for name in account_name_renderings() if name in rendered)

    assert leaked == 0, "a local-config skip record carried an account name rendering"
    assert warnings, "the discard produced no skip record at all"
    assert warnings[0].detail, "a skip record named no reason at all"


def test_reporting_channel_does_not_change_resolution_behaviour(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """_override() calls local_config() with no collector and must be unaffected.

    Resolution is the hot path and the one an operator actually depends on;
    adding a report channel to the reader underneath it must not move a single
    resolution outcome. A malformed config still resolves to auto-detection
    exactly as before, and a good one still overrides.
    """
    good = tmp_path / "install"
    good.mkdir()
    _write_local_config(monkeypatch, tmp_path, {locate.CONFIG_GAME_DIR: str(good)})

    assert locate.resolve_game_dir() == (good, f"config:{locate.CONFIG_GAME_DIR}")

    _write_local_config(monkeypatch, tmp_path, "{ this is not json")
    monkeypatch.setattr(locate, "_steam_library_paths", list)
    monkeypatch.setattr(locate, "_drive_roots", lambda: [tmp_path])

    assert locate.resolve_game_dir() == (None, "unresolved")


# ---------------------------------------------------------------------------
# Redaction - the leak paths
# ---------------------------------------------------------------------------


def test_redact_hides_an_account_id_shaped_directory(tmp_path: Path) -> None:
    rendered = locate.redact(tmp_path / NEWEST_FAKE_ACCOUNT_ID / "world.sav")

    leaked = NEWEST_FAKE_ACCOUNT_ID in rendered
    assert not leaked, "redact() left an account-id-shaped directory in its output"
    assert locate.ACCOUNT_DIR_PLACEHOLDER in rendered


def test_redact_hides_a_home_prefix(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    local = home / "AppData" / "Local"
    local.mkdir(parents=True)
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("LOCALAPPDATA", str(local))

    rendered = locate.redact(local / "FactoryGame" / "Saved")

    leaked = home.as_posix() in rendered
    assert not leaked, "redact() left an absolute home path in its output"
    assert "FactoryGame/Saved" in rendered


def test_a_resolved_account_dir_renders_without_the_account_id_or_the_home_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The whole leak path end to end: resolve a real-shaped account directory
    # under a fake home, then render it the way a message or an exception
    # would. Both the id and the home prefix have to be gone, and the tokens
    # have to be present - a negative assertion alone rules out without
    # pinning down (CONVENTIONS.md section 7.2).
    home = tmp_path / "home"
    local = home / "AppData" / "Local"
    save_root = local.joinpath(*locate.SAVE_ROOT_PARTS)
    save_root.mkdir(parents=True)
    _make_account_dir(save_root, NEWEST_FAKE_ACCOUNT_ID)
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("LOCALAPPDATA", str(local))

    resolved = locate.resolve_account_dir(locate.resolve_save_root())
    rendered = locate.redact(resolved)

    leaked_id = NEWEST_FAKE_ACCOUNT_ID in rendered
    leaked_home = home.as_posix() in rendered
    assert not leaked_id, "a rendered account directory leaked the account id"
    assert not leaked_home, "a rendered account directory leaked the home path"
    assert locate.ACCOUNT_DIR_PLACEHOLDER in rendered
    assert "FactoryGame/Saved/SaveGames" in rendered


def test_redact_leaves_an_ordinary_path_readable() -> None:
    rendered = locate.redact(Path("D:/Games/Steam/steamapps/common"))

    assert rendered == "D:/Games/Steam/steamapps/common"


# ---------------------------------------------------------------------------
# Redaction - the five shapes, each one a reproduced leak
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "account_dir"), ACCOUNT_DIR_SHAPES, ids=[s[0] for s in ACCOUNT_DIR_SHAPES]
)
def test_redact_hides_an_account_directory_of_any_shape(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, label: str, account_dir: str
) -> None:
    """Whatever occupies the account-id position is personal data.

    The account directory is identified by POSITION - the segment immediately
    below the save root - and never by what its characters look like. Steam
    writes digits there, Epic a hex token, the Microsoft Store a GUID, and the
    documented override writes whatever the operator typed.

    WHAT THIS LAYOUT CAN AND CANNOT OBSERVE (CS-454, ADR 0008). Every path
    built here spells the save-root marker, so POSITION fires for all four
    shapes: neutering the positional rule alone leaves three of these four
    leaking, and neutering the digit backstop alone leaves none of them
    leaking. Varying the shape therefore pins "position catches every shape"
    and nothing shape-dependent. The shapes a non-positional rule has to reach
    are covered by the relocated-save-root tests below, where there is no
    marker for position to key on.
    """
    home = tmp_path / "home"
    local = home / "AppData" / "Local"
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("LOCALAPPDATA", str(local))
    path = local.joinpath(*locate.SAVE_ROOT_PARTS) / account_dir / "some-file.dat"

    rendered = locate.redact(path)

    leaked = account_dir.lower() in rendered.lower()
    assert not leaked, f"redact() left a {label} account directory in its output"
    assert locate.ACCOUNT_DIR_PLACEHOLDER in rendered
    assert "FactoryGame/Saved/SaveGames" in rendered, (
        "the account directory went, but so did the structure around it - a negative "
        "assertion alone rules out without pinning down (CONVENTIONS.md section 7.2)"
    )


def test_redact_hides_every_rendering_of_the_account_name_including_the_8_3_short_form() -> None:
    """The 8.3 short path is a home path that no environment value spells.

    Windows keeps a legacy 8.3 name for most directories, and on a default
    install tempfile.gettempdir() returns one - so a temporary path arrives
    carrying the first six characters of the account name plus a tilde and a
    digit. It matches no long-form environment value, and the account name is
    not a substring of it, so a redactor built only from the environment
    leaves it standing and the operator's account name reaches the log.

    The renderings come from the operating system, never from redact() - see
    account_name_renderings().
    """
    renderings = account_name_renderings()
    too_short = sum(1 for name in renderings if len(name) < locate.MIN_REDACTABLE_LEN)
    if too_short:
        pytest.skip(
            f"{too_short} rendering(s) of this machine's account name are shorter than "
            "the redaction floor, so no needle could safely be built from them"
        )
    probe = Path(tempfile.gettempdir()) / "clockspeed-probe" / "artifact.log"

    rendered = locate.redact(probe)

    # A COUNT, never the names. Binding the offending strings to a local is
    # enough to publish them: pytest reprs every local it can reach in the
    # "assert" line of a failure, so a list here would print the account name
    # into the CI log on the very run that proves it must not be printed.
    leaked = sum(1 for name in renderings if name.lower() in rendered.lower())
    assert not leaked, (
        f"redact() left {leaked} of {len(renderings)} rendering(s) of the account "
        "name in its output (content withheld)"
    )


def test_redact_hides_an_account_directory_an_override_placed_outside_the_save_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An override that relocates the account directory is still personal data.

    CLOCKSPEED_ACCOUNT_DIR and config/local.json "account_dir" accept an
    absolute path, so the directory need not sit under the save root at all.
    There is then no marker for it to sit below and, unless the operator chose
    digits, no digit run either - position and pattern both miss it. What the
    resolver hands out is what has to be redactable.
    """
    save_root = _make_save_root(tmp_path)
    _make_account_dir(save_root, NEWEST_FAKE_ACCOUNT_ID)
    relocated = tmp_path / "backup" / "a1b2c3d4e5f60718293a4b5c6d7e8f90"
    relocated.mkdir(parents=True)
    monkeypatch.setenv(locate.ENV_ACCOUNT_DIR, str(relocated))

    resolved = locate.resolve_account_dir(save_root)
    assert resolved == relocated, "the override did not resolve; this test would prove nothing"
    rendered = locate.redact(resolved)

    leaked = relocated.name.lower() in rendered.lower()
    assert not leaked, "a relocated account directory leaked its name"
    assert locate.ACCOUNT_DIR_PLACEHOLDER in rendered


def test_redact_hides_the_segment_below_a_declared_but_relocated_save_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A save root the operator moved still has an account id under it (CS-454).

    THE CONJUNCTION THIS CONTROL SATISFIES, because two of the three were
    missing from every account-directory control before it:

      (a) the account name is a HEX TOKEN, not digits, so the digit backstop
          cannot reach it;
      (b) the declared save root does NOT spell FactoryGame/Saved/SaveGames,
          so the POSITIONAL rule has no marker to key on - asserted below
          rather than assumed, because if the marker were present position
          would fire and mask the shape entirely;
      (c) the rule under mutation is therefore the new save-root ANCHOR set;
          removing it leaves this account name standing in plaintext.

    Nothing is resolved through the module first, so the account-name memory
    is empty too: the declared save root read straight from the environment is
    the only thing that can carry this.
    """
    relocated = tmp_path / "Relocated" / "operator_chosen_saves"
    account = relocated / "a1b2c3d4e5f60718293a4b5c6d7e8f90"
    account.mkdir(parents=True)
    monkeypatch.setenv(locate.ENV_SAVE_ROOT, str(relocated))
    assert "FactoryGame/Saved/SaveGames" not in relocated.as_posix(), (
        "the relocated root spells the marker, so POSITION would fire and this "
        "test would prove nothing about the anchor set"
    )

    rendered = locate.redact(account / "World.dat")

    leaked = account.name.lower() in rendered.lower()
    assert not leaked, "redact() left the account directory below a relocated save root"
    assert locate.ACCOUNT_DIR_PLACEHOLDER in rendered
    assert rendered.endswith(f"/{locate.ACCOUNT_DIR_PLACEHOLDER}/World.dat"), (
        "the account directory went, but so did the structure around it - a negative "
        "assertion alone rules out without pinning down (CONVENTIONS.md section 7.2)"
    )


def test_redact_hides_the_segment_below_a_save_root_it_has_already_resolved(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A resolved save root stays an anchor after the declaration goes (CS-454).

    Same conjunction as the test above - (a) a hex token, (b) no marker for
    POSITION, (c) the anchor set is the rule under mutation - with one
    difference that is the whole point: CLOCKSPEED_SAVE_ROOT is DELETED after
    the resolver has run. Reading the environment cannot answer here, so the
    only thing left standing between this account id and the output is the
    remembered-save-root memory that resolve_save_root() fills.
    """
    relocated = tmp_path / "Relocated" / "operator_chosen_saves"
    account = relocated / "a1b2c3d4e5f60718293a4b5c6d7e8f90"
    account.mkdir(parents=True)
    monkeypatch.setenv(locate.ENV_SAVE_ROOT, str(relocated))

    resolved = locate.resolve_save_root()
    assert resolved == relocated, "the override did not resolve; this test would prove nothing"
    monkeypatch.delenv(locate.ENV_SAVE_ROOT)

    rendered = locate.redact(account / "World.dat")

    leaked = account.name.lower() in rendered.lower()
    assert not leaked, "a resolved save root stopped anchoring once the declaration went"
    assert locate.ACCOUNT_DIR_PLACEHOLDER in rendered
    assert rendered.endswith(f"/{locate.ACCOUNT_DIR_PLACEHOLDER}/World.dat"), (
        "the account directory went, but so did the structure around it"
    )


def test_redact_hides_the_8_3_rendering_of_an_account_directory_it_handed_out(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The declared account directory has a second spelling, and it leaked.

    THE DEFECT (CS-454). This module already knows that Windows renders a path
    two ways and that the 8.3 short form matches no long-form value - the
    module docstring says so, and _path_forms() exists for exactly that reason
    on the HOME directory. It was applied to neither the marker nor the account
    name, so the short rendering of the account directory reached the output in
    plaintext EVEN WITH CLOCKSPEED_ACCOUNT_DIR declared, which is the
    configuration resolve_account_dir() documents as the safe one.

    The conjunction: (a) the name is not digits; (b) the 8.3 rendering does not
    spell the marker either - asserted below - so POSITION cannot fire; (c) the
    rule under mutation is _remember_account_dir()'s new use of _path_forms().
    """
    save_root = _make_save_root(tmp_path)
    account = _make_account_dir(save_root, "EpicAccountTokenLongEnoughToShorten")
    monkeypatch.setenv(locate.ENV_ACCOUNT_DIR, str(account))

    resolved = locate.resolve_account_dir(save_root)
    assert resolved == account, "the override did not resolve; this test would prove nothing"
    short = locate._win_path_form(str(account), "GetShortPathNameW")  # noqa: SLF001
    if short is None or Path(short).name.lower() == account.name.lower():
        pytest.skip("this volume has no distinct 8.3 rendering, so there is no second spelling")
    short_name = Path(short).name
    if len(short_name) < locate.MIN_REDACTABLE_LEN:
        pytest.skip("the 8.3 rendering is shorter than the redaction floor")
    assert "FactoryGame/Saved/SaveGames" not in short.replace("\\", "/"), (
        "the 8.3 rendering still spells the marker, so POSITION could fire and this "
        "test would not isolate the rule it names"
    )

    rendered = locate.redact(short)

    leaked = short_name.lower() in rendered.lower()
    assert not leaked, "redact() left the 8.3 rendering of the account directory in its output"
    assert rendered.endswith(locate.ACCOUNT_DIR_PLACEHOLDER), (
        "the short account name went, but the path around it did not survive"
    )


def test_redact_hides_a_world_name_carried_by_a_save_filename(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A save filename embeds the world name, which CLAUDE.md rule 3 protects.

    There is no way to tell a world name from any other filename stem without
    parsing the save, so the whole filename component goes. Phase 3 hands this
    module save paths; the redactor has to be right before it does.
    """
    home = tmp_path / "home"
    local = home / "AppData" / "Local"
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("LOCALAPPDATA", str(local))
    save = (
        local.joinpath(*locate.SAVE_ROOT_PARTS)
        / NEWEST_FAKE_ACCOUNT_ID
        / f"{FAKE_WORLD_NAME}_autosave_0.sav"
    )

    rendered = locate.redact(save)

    leaked = FAKE_WORLD_NAME.lower() in rendered.lower()
    assert not leaked, "redact() left a world name in a save filename"
    assert locate.SAVE_FILE_PLACEHOLDER in rendered
    assert "FactoryGame/Saved/SaveGames" in rendered


def test_redact_is_idempotent_so_a_placeholder_survives_a_second_pass(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Redacting twice says the same thing as redacting once.

    Output is redacted at more than one seam - a skip record built by a guard
    is redacted again when it is rendered - so a redactor that chewed its own
    placeholders would produce a different string each time it passed a layer.
    """
    home = tmp_path / "home"
    local = home / "AppData" / "Local"
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("LOCALAPPDATA", str(local))
    path = local.joinpath(*locate.SAVE_ROOT_PARTS) / NEWEST_FAKE_ACCOUNT_ID / "world.sav"

    once = locate.redact(path)

    assert locate.redact(once) == once


# ---------------------------------------------------------------------------
# Live install - skipped rather than failed when the game is absent
# ---------------------------------------------------------------------------


def test_live_detection_answers_with_a_real_directory_when_the_game_is_installed() -> None:
    """Exercise real auto-detection, and skip loudly where there is no install.

    A test that needs the game must skip with a reason rather than fail or
    silently pass (CS-200). The resolved path is never printed unredacted.
    """
    game_dir, source = locate.resolve_game_dir()
    if game_dir is None:
        pytest.skip(f"no game install on this machine; the resolver reported: {source}")

    is_directory = game_dir.is_dir()
    assert is_directory, "auto-detection returned a path that is not a directory"
    assert source in {"steam-library-index", "default-location"}
