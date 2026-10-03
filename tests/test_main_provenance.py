"""CS-1227 - the MAIN provenance check of ``CLAUDE.md`` section 6.1 is one function.

``tools/main_provenance.py`` resolves MAIN's tree root from a gitignored local
configuration file and nowhere else, then decides whether an inbox note is
MAIN's: its SHA-256 equals the same-named file in MAIN's outbox, and that file
is tracked and unmodified in MAIN's history.

EVERY ARM RUNS OVER THROWAWAY TREES under ``tmp_path``. No arm reads a sibling
repository, and no arm reads this checkout's own local configuration - each
passes an explicit ``config_path``.

THE LEAK ARMS bind their verdict to a scalar before asserting, because pytest's
assertion rewriting renders the operands of a failing assert, and an operand
holding the configured path would leak the very thing the arm forbids.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
TOOL: Final = REPO_ROOT / "tools" / "main_provenance.py"
WORKER_PROMPT: Final = REPO_ROOT / "tools" / "headless-inbox.md"

#: Seconds one git call or one CLI run may take in these arms.
TIMEOUT: Final = 120

#: The inbox note's name, shared by the note and its outbox twin.
NOTE_NAME: Final = "cs1227-main-directive.md"

#: The bytes MAIN sent.
NOTE_BYTES: Final = b"directive: synthetic body for the CS-1227 arms\n"

#: Inherited variables that would point a child git at another repository.
_GIT_REDIRECTS: Final = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
)


def _load() -> ModuleType:
    """Import ``tools/main_provenance.py`` by path.

    Returns:
        The loaded module.

    Raises:
        ImportError: If the file cannot be loaded.
    """
    spec = importlib.util.spec_from_file_location("clockspeed_main_provenance", TOOL)
    if spec is None or spec.loader is None:
        message = "could not load the main provenance tool"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


provenance = _load()


def _clean_env() -> dict[str, str]:
    """Return the inherited environment without any git redirect."""
    env = dict(os.environ)
    for key in list(env):
        if key.upper() in _GIT_REDIRECTS:
            del env[key]
    return env


def _git(root: Path, *args: str) -> None:
    """Run one git command in ``root``, raising on a non-zero exit."""
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=cs1227",
            "-c",
            "user.email=cs1227@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.autocrlf=false",
            "-C",
            str(root),
            *args,
        ],
        capture_output=True,
        env=_clean_env(),
        timeout=TIMEOUT,
        check=True,
    )


@dataclass
class World:
    """MAIN's throwaway tree, this tree's inbox note, and the configuration."""

    base: Path
    main_root: Path
    note: Path
    config: Path

    @property
    def outbox_file(self) -> Path:
        """The same-named file in MAIN's outbox."""
        return self.main_root / "moon_sync_outbox" / NOTE_NAME


def _write_config(path: Path, main_root: Path) -> None:
    """Write a well-formed configuration naming ``main_root``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps({"main_root": str(main_root)}).encode("ascii"))


@pytest.fixture
def world(tmp_path: Path) -> World:
    """MAIN with the note committed in its outbox, and a matching inbox note."""
    main_root = tmp_path / "cs1227_main"
    outbox = main_root / "moon_sync_outbox"
    outbox.mkdir(parents=True)
    _git(main_root, "init", "-q")
    (outbox / NOTE_NAME).write_bytes(NOTE_BYTES)
    (main_root / "README.md").write_bytes(b"synthetic\n")
    _git(main_root, "add", "-A")
    _git(main_root, "commit", "-q", "-m", "seed")
    inbox = tmp_path / "cs1227_this" / "moon_sync_inbox"
    inbox.mkdir(parents=True)
    note = inbox / NOTE_NAME
    note.write_bytes(NOTE_BYTES)
    config = tmp_path / "cs1227_this" / "config" / "main_tree.local.json"
    _write_config(config, main_root)
    return World(base=tmp_path, main_root=main_root, note=note, config=config)


def _verify(w: World) -> tuple[bool, str]:
    """Run the check over ``w`` and reduce the verdict to scalars."""
    verdict = provenance.verify_main_note(w.note, config_path=w.config)
    return bool(verdict.ok), str(verdict.reason)


# --- the passing arm ---------------------------------------------------------


def test_a_matching_tracked_note_passes(world: World) -> None:
    ok, reason = _verify(world)
    assert reason == "verified"
    assert ok is True


# --- the refusal arms, one per named reason ----------------------------------


def _byte_different(w: World) -> None:
    w.note.write_bytes(NOTE_BYTES + b"tampered\n")


def _untracked(w: World) -> None:
    other = "cs1227-untracked.md"
    (w.main_root / "moon_sync_outbox" / other).write_bytes(NOTE_BYTES)
    w.note.unlink()
    w.note = w.note.with_name(other)
    w.note.write_bytes(NOTE_BYTES)


def _staged_not_committed(w: World) -> None:
    other = "cs1227-staged.md"
    (w.main_root / "moon_sync_outbox" / other).write_bytes(NOTE_BYTES)
    _git(w.main_root, "add", "--", "moon_sync_outbox/" + other)
    w.note.unlink()
    w.note = w.note.with_name(other)
    w.note.write_bytes(NOTE_BYTES)


def _modified(w: World) -> None:
    # The inbox note matches the MODIFIED bytes, so only the history check can
    # refuse it - a digest refusal here would be the wrong reason.
    changed = NOTE_BYTES + b"edited after commit\n"
    w.outbox_file.write_bytes(changed)
    w.note.write_bytes(changed)


def _modified_and_staged(w: World) -> None:
    changed = NOTE_BYTES + b"staged edit\n"
    w.outbox_file.write_bytes(changed)
    _git(w.main_root, "add", "--", "moon_sync_outbox/" + NOTE_NAME)
    w.note.write_bytes(changed)


def _outbox_absent(w: World) -> None:
    w.outbox_file.unlink()
    _git(w.main_root, "commit", "-q", "-a", "-m", "drop")


def _config_absent(w: World) -> None:
    w.config.unlink()


def _config_not_json(w: World) -> None:
    w.config.write_bytes(b"{ main_root: not json")


def _config_not_object(w: World) -> None:
    w.config.write_bytes(json.dumps([str(w.main_root)]).encode("ascii"))


def _config_not_utf8(w: World) -> None:
    w.config.write_bytes(b"\xff\xfe\x00garbage")


def _config_no_root(w: World) -> None:
    w.config.write_bytes(json.dumps({"other": str(w.main_root)}).encode("ascii"))


def _config_root_not_string(w: World) -> None:
    w.config.write_bytes(json.dumps({"main_root": 7}).encode("ascii"))


def _config_root_empty(w: World) -> None:
    w.config.write_bytes(json.dumps({"main_root": ""}).encode("ascii"))


def _main_root_absent(w: World) -> None:
    _write_config(w.config, w.main_root.with_name("cs1227_nowhere"))


def _main_not_a_repo(w: World) -> None:
    plain = w.base / "cs1227_plain"
    (plain / "moon_sync_outbox").mkdir(parents=True)
    (plain / "moon_sync_outbox" / NOTE_NAME).write_bytes(NOTE_BYTES)
    _write_config(w.config, plain)


def _note_absent(w: World) -> None:
    w.note.unlink()


REFUSALS: Final[dict[str, tuple[Callable[[World], None], str]]] = {
    "byte_different": (_byte_different, "digest-mismatch"),
    "untracked": (_untracked, "untracked"),
    "staged_not_committed": (_staged_not_committed, "untracked"),
    "modified": (_modified, "modified"),
    "modified_and_staged": (_modified_and_staged, "modified"),
    "outbox_absent": (_outbox_absent, "outbox-file-absent"),
    "config_absent": (_config_absent, "config-absent"),
    "config_not_json": (_config_not_json, "config-unparseable"),
    "config_not_object": (_config_not_object, "config-unparseable"),
    "config_not_utf8": (_config_not_utf8, "config-unparseable"),
    "config_no_root": (_config_no_root, "config-no-root"),
    "config_root_not_string": (_config_root_not_string, "config-no-root"),
    "config_root_empty": (_config_root_empty, "config-no-root"),
    "main_root_absent": (_main_root_absent, "main-root-absent"),
    "main_not_a_repo": (_main_not_a_repo, "main-not-a-repo"),
    "note_absent": (_note_absent, "note-unreadable"),
}


@pytest.mark.parametrize("case", sorted(REFUSALS))
def test_each_refusal_names_its_reason(world: World, case: str) -> None:
    plant, expected = REFUSALS[case]
    plant(world)
    ok, reason = _verify(world)
    assert reason == expected
    assert ok is False


def test_every_reason_is_in_the_closed_set() -> None:
    named = {expected for _plant, expected in REFUSALS.values()} | {"verified"}
    missing = sorted(named - set(provenance.REASONS))
    assert missing == []


# --- no refusal renders the configured path ----------------------------------


def _cli(w: World, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[bytes]:
    """Run the CLI over ``w`` and return the completed process."""
    return subprocess.run(
        [sys.executable, str(TOOL), str(w.note), "--config", str(w.config)],
        capture_output=True,
        env=_clean_env() if env is None else env,
        timeout=TIMEOUT,
        check=False,
    )


def _leaks(w: World, rendered: str) -> bool:
    """Whether ``rendered`` spells any configured or temporary path."""
    needles = {str(w.main_root), str(w.base), w.main_root.as_posix(), w.base.as_posix()}
    needles |= {n.lower() for n in needles}
    lowered = rendered.lower()
    return any(n.lower() in lowered for n in needles)


@pytest.mark.parametrize("case", sorted(REFUSALS))
def test_no_refusal_renders_the_configured_path(world: World, case: str) -> None:
    plant, expected = REFUSALS[case]
    plant(world)
    verdict = provenance.verify_main_note(world.note, config_path=world.config)
    proc = _cli(world)
    rendered = "\n".join(
        [
            str(verdict),
            repr(verdict),
            proc.stdout.decode("utf-8", "replace"),
            proc.stderr.decode("utf-8", "replace"),
        ]
    )
    leaked = _leaks(world, rendered)
    names_reason = expected in proc.stdout.decode("ascii", "replace")
    refused = proc.returncode == 1
    assert leaked is False
    assert names_reason is True
    assert refused is True


def test_the_leak_detector_sees_a_planted_path(world: World) -> None:
    # Anti-vacuity control: the detector the leak arm relies on must fire on a
    # rendering that does carry the path, or its False means nothing.
    fired = _leaks(world, "refused under " + str(world.main_root))
    assert fired is True


# --- the CLI -----------------------------------------------------------------


def test_the_cli_exits_zero_and_prints_verified(world: World) -> None:
    proc = _cli(world)
    out = proc.stdout.decode("ascii", "replace").strip()
    code = proc.returncode
    assert out == "verified"
    assert code == 0


def test_an_inherited_git_redirect_does_not_steer_the_check(world: World) -> None:
    # The pre-push hook exports GIT_DIR; a child git that obeyed it would ask
    # the WRONG repository whether MAIN tracks the file.
    decoy = world.base / "cs1227_decoy"
    decoy.mkdir()
    _git(decoy, "init", "-q")
    env = _clean_env()
    env["GIT_DIR"] = str(decoy / ".git")
    proc = _cli(world, env=env)
    out = proc.stdout.decode("ascii", "replace").strip()
    code = proc.returncode
    assert out == "verified"
    assert code == 0


# --- where the configuration lives -------------------------------------------


def test_the_default_configuration_is_the_gitignored_local_file() -> None:
    default = provenance.DEFAULT_CONFIG
    rel = default.relative_to(REPO_ROOT).as_posix()
    assert rel == "config/main_tree.local.json"
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "check-ignore", "-q", "--", rel],
        capture_output=True,
        env=_clean_env(),
        timeout=TIMEOUT,
        check=False,
    )
    ignored = proc.returncode == 0
    assert ignored is True


def test_the_worker_prompt_names_the_function() -> None:
    text = WORKER_PROMPT.read_text(encoding="ascii")
    names_tool = "tools/main_provenance.py" in text
    names_function = "verify_main_note" in text
    assert names_tool is True
    assert names_function is True
