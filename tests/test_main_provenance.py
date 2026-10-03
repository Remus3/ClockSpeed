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

import hashlib
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

#: The SHA-256 hex a verified verdict must carry for NOTE_BYTES.
NOTE_SHA256: Final = hashlib.sha256(NOTE_BYTES).hexdigest()

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


def _git(root: Path, *args: str) -> str:
    """Run one git command in ``root`` and return its stripped stdout.

    Fails the test on a non-zero exit.

    The failure names only the git subcommand. ``check=True`` would raise a
    ``CalledProcessError`` whose rendering carries the temporary root.
    """
    proc = subprocess.run(
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
        check=False,
    )
    failed = proc.returncode != 0
    if failed:
        pytest.fail("fixture git step failed: " + args[0], pytrace=False)
    return proc.stdout.decode("ascii", "replace").strip()


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
    verdict = provenance.verify_main_note(world.note, config_path=world.config)
    reason = str(verdict.reason)
    ok = bool(verdict.ok)
    digest = str(verdict.digest)
    # The verdict binds to the bytes it verified, so a caller can refuse a note
    # that changed after the check.
    assert reason == "verified"
    assert ok is True
    assert digest == NOTE_SHA256


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


# A1 - git's stat cache must never stand in for the committed bytes. Each plant
# below leaves `git diff --quiet HEAD` reporting clean while the working-tree
# file differs from HEAD's blob, and the inbox note matches the WORKING bytes.

_EDITED: Final = NOTE_BYTES.replace(b"synthetic", b"SYNTHETIC")


def _flagged_edit(w: World, flag: str) -> None:
    _git(w.main_root, "update-index", flag, "--", "moon_sync_outbox/" + NOTE_NAME)
    w.outbox_file.write_bytes(_EDITED)
    w.note.write_bytes(_EDITED)


def _assume_unchanged(w: World) -> None:
    _flagged_edit(w, "--assume-unchanged")


def _skip_worktree(w: World) -> None:
    _flagged_edit(w, "--skip-worktree")


def _same_size_mtime_restored(w: World) -> None:
    # Age the file, refresh the index so its stat entry records the old mtime
    # (and the index itself is newer, so the entry is not racily clean), then
    # rewrite the same number of bytes and put the old mtime back.
    old = 1_000_000_000
    os.utime(w.outbox_file, (old, old))
    _git(w.main_root, "update-index", "--refresh")
    w.outbox_file.write_bytes(_EDITED)
    os.utime(w.outbox_file, (old, old))
    w.note.write_bytes(_EDITED)


def _staged_edit_then_restored(w: World) -> None:
    # The index holds bytes HEAD never committed; the working tree is back to
    # HEAD's. The committed blob is the only truth, and the index disagrees.
    w.outbox_file.write_bytes(_EDITED)
    _git(w.main_root, "add", "--", "moon_sync_outbox/" + NOTE_NAME)
    w.outbox_file.write_bytes(NOTE_BYTES)


def _config_deeply_nested(w: World) -> None:
    # B1 - the JSON decoder raises RecursionError on this, which is not a
    # ValueError.
    w.config.write_bytes(b"[" * 200_000)


def _corrupt_gitdir(w: World) -> None:
    # B2 - a root whose `.git` file points nowhere makes git print that path on
    # stderr. The check must capture it and render nothing.
    broken = w.base / "cs1227_broken"
    (broken / "moon_sync_outbox").mkdir(parents=True)
    (broken / "moon_sync_outbox" / NOTE_NAME).write_bytes(NOTE_BYTES)
    gone = (w.base / "cs1227_gone_gitdir").as_posix()
    (broken / ".git").write_bytes(("gitdir: " + gone + "\n").encode("utf-8"))
    _write_config(w.config, broken)


# Round 2 - replace refs. git follows `refs/replace/` in rev-parse and cat-file
# unless told not to, so a replacement makes never-committed bytes look like
# HEAD's. In both plants the note and the working tree carry the EVIL bytes.

_EVIL: Final = b"directive: never committed by MAIN\n"


def _evil_blob(w: World) -> str:
    """Write the evil bytes as a loose blob in MAIN and return its id."""
    source = w.base / "cs1227_evil_source"
    source.write_bytes(_EVIL)
    return _git(w.main_root, "hash-object", "-w", "--", str(source))


def _replaced_blob(w: World) -> None:
    rel = "moon_sync_outbox/" + NOTE_NAME
    original = _git(w.main_root, "rev-parse", "HEAD:" + rel)
    _git(w.main_root, "replace", original, _evil_blob(w))
    w.outbox_file.write_bytes(_EVIL)
    w.note.write_bytes(_EVIL)


def _replaced_head_commit(w: World) -> None:
    # A side commit carries the evil bytes; HEAD's commit is then REPLACED by
    # it, and the index re-read through the replacement so index and
    # (replaced) HEAD agree.
    original = _git(w.main_root, "rev-parse", "HEAD")
    _git(w.main_root, "checkout", "-q", "-b", "cs1227-side")
    w.outbox_file.write_bytes(_EVIL)
    _git(w.main_root, "commit", "-q", "-a", "-m", "evil")
    fake = _git(w.main_root, "rev-parse", "HEAD")
    _git(w.main_root, "checkout", "-q", "-")
    _git(w.main_root, "replace", original, fake)
    _git(w.main_root, "read-tree", "HEAD")
    w.outbox_file.write_bytes(_EVIL)
    w.note.write_bytes(_EVIL)


def _shallow_clone(w: World) -> None:
    # A shallow repository's history is cut off by a graft-like file; refuse
    # it outright rather than reason about what the cut hides.
    (w.main_root / "README.md").write_bytes(b"second\n")
    _git(w.main_root, "commit", "-q", "-a", "-m", "second")
    _git(w.base, "clone", "-q", "--depth", "1", w.main_root.as_uri(), "cs1227_shallow")
    _write_config(w.config, w.base / "cs1227_shallow")


def _crlf_checkout(w: World) -> None:
    # Ruling A, round 3 - a checkout filter rewrites the bytes on disk while
    # git reports the tree clean. `.gitattributes` rather than core.autocrlf, so
    # Linux CI behaves the same. The note carries the COMMITTED (LF) bytes, so
    # only the working-tree comparison can refuse.
    (w.main_root / ".gitattributes").write_bytes(b"* text eol=crlf\n")
    _git(w.main_root, "add", "--", ".gitattributes")
    _git(w.main_root, "commit", "-q", "-m", "eol")
    w.outbox_file.unlink()
    _git(w.main_root, "checkout", "--", "moon_sync_outbox/" + NOTE_NAME)


#: Every refusal where the working-tree file differs from HEAD's blob while the
#: index agrees with HEAD - distinct from an index that disagrees (`modified`).
_DIFFERS: Final = "worktree-differs-from-commit"


REFUSALS: Final[dict[str, tuple[Callable[[World], None], str]]] = {
    "replaced_blob": (_replaced_blob, _DIFFERS),
    "replaced_head_commit": (_replaced_head_commit, "modified"),
    "shallow_clone": (_shallow_clone, "main-shallow"),
    "crlf_checkout": (_crlf_checkout, _DIFFERS),
    "byte_different": (_byte_different, "digest-mismatch"),
    "untracked": (_untracked, "untracked"),
    "staged_not_committed": (_staged_not_committed, "untracked"),
    "modified": (_modified, _DIFFERS),
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
    "assume_unchanged": (_assume_unchanged, _DIFFERS),
    "skip_worktree": (_skip_worktree, _DIFFERS),
    "same_size_mtime_restored": (_same_size_mtime_restored, _DIFFERS),
    "staged_edit_then_restored": (_staged_edit_then_restored, "modified"),
    "config_deeply_nested": (_config_deeply_nested, "config-unparseable"),
    "corrupt_gitdir": (_corrupt_gitdir, "main-not-a-repo"),
}


def test_a_filtered_checkout_git_calls_clean_is_refused(world: World) -> None:
    # Pins fail-closed behaviour (Ruling A): git says clean, the bytes on disk
    # are CRLF, HEAD's blob is LF - refused, and nothing renders a path.
    _crlf_checkout(world)
    on_disk_crlf = b"\r\n" in world.outbox_file.read_bytes()
    porcelain = _git(world.main_root, "status", "--porcelain")
    git_clean = porcelain == ""
    ok, reason = _verify(world)
    proc = _cli(world)
    rendered = proc.stdout.decode("utf-8", "replace") + proc.stderr.decode("utf-8", "replace")
    leaked = _leaks(world, rendered + reason)
    assert on_disk_crlf is True
    assert git_clean is True
    assert reason == _DIFFERS
    assert ok is False
    assert leaked is False


@pytest.mark.parametrize("case", sorted(REFUSALS))
def test_each_refusal_names_its_reason(world: World, case: str) -> None:
    plant, expected = REFUSALS[case]
    plant(world)
    verdict = provenance.verify_main_note(world.note, config_path=world.config)
    reason = str(verdict.reason)
    ok = bool(verdict.ok)
    digest = str(verdict.digest)
    assert reason == expected
    assert ok is False
    assert digest == ""


def test_every_reason_is_in_the_closed_set() -> None:
    named = {expected for _plant, expected in REFUSALS.values()}
    named |= {"verified", "config-root-not-absolute", "check-failed", "interrupted"}
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


def _short_form(path: Path) -> str | None:
    """The Windows 8.3 short spelling of ``path``, or None where unobtainable."""
    if sys.platform != "win32":
        return None
    import ctypes  # noqa: PLC0415 - Windows-only, and only for this needle

    buf = ctypes.create_unicode_buffer(1024)
    got = ctypes.windll.kernel32.GetShortPathNameW(str(path), buf, len(buf))
    return buf.value if 0 < got < len(buf) else None


def _spellings(path: Path) -> set[str]:
    """Every way a rendering could spell ``path``: native, POSIX, repr-escaped, 8.3."""
    native = str(path)
    forms = {native, path.as_posix(), native.replace("\\", "\\\\"), repr(native)[1:-1]}
    short = _short_form(path)
    if short:
        forms |= {short, short.replace("\\", "\\\\"), short.replace("\\", "/")}
    return forms


def _leaks(w: World, rendered: str) -> bool:
    """Whether ``rendered`` spells any configured, temporary or home path."""
    needles: set[str] = set()
    for path in (w.main_root, w.base, Path.home()):
        needles |= _spellings(path)
    lowered = rendered.lower()
    return any(n.lower() in lowered for n in needles if n)


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
    traceback = "Traceback" in rendered
    names_reason = proc.stdout.decode("ascii", "replace").strip() == expected
    refused = proc.returncode == 1
    assert leaked is False
    assert traceback is False
    assert names_reason is True
    assert refused is True


@pytest.mark.parametrize(
    "spell",
    [
        str,
        Path.as_posix,
        lambda p: repr(str(p)),
        lambda p: str(p).replace("\\", "\\\\"),
    ],
    ids=["native", "posix", "repr", "doubled"],
)
def test_the_leak_detector_sees_a_planted_path(world: World, spell: Callable[[Path], str]) -> None:
    # Anti-vacuity control: the detector the leak arm relies on must fire on a
    # rendering that does carry the path, in every spelling, or its False
    # means nothing.
    fired = _leaks(world, "refused under " + spell(world.main_root))
    assert fired is True


def _explode(*_args: object, **_kwargs: object) -> None:
    message = "cs1227 planted failure"
    raise RuntimeError(message)


def test_an_unexpected_failure_is_a_named_refusal(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    # B1 - verify_main_note never raises: any failure inside a step becomes a
    # fixed reason, and the planted message is dropped.
    monkeypatch.setattr(provenance, "_main_root", _explode)
    ok, reason = _verify(world)
    assert reason == "check-failed"
    assert ok is False


def _interrupt(*_args: object, **_kwargs: object) -> None:
    raise KeyboardInterrupt


def test_the_cli_turns_an_interrupt_into_a_reason(
    world: World, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(provenance, "verify_main_note", _interrupt)
    code = provenance.main([str(world.note), "--config", str(world.config)])
    captured = capsys.readouterr()
    out = captured.out.strip()
    quiet = captured.err == ""
    assert out == "interrupted"
    assert code == 1
    assert quiet is True


def test_the_leak_detector_sees_the_short_form(world: World) -> None:
    short = _short_form(world.main_root)
    if short is None:
        pytest.skip("no 8.3 short form on this platform or volume")
    fired = _leaks(world, "refused under " + short)
    assert fired is True


def test_a_relative_main_root_refuses_whatever_the_cwd(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A2 - a relative root would resolve against the cwd, so a worker started
    # beside a look-alike tree would verify against it. Here the cwd makes the
    # relative spelling land on the REAL fixture, so only the absoluteness rule
    # can refuse it.
    w = world
    w.config.write_bytes(json.dumps({"main_root": w.main_root.name}).encode("ascii"))
    monkeypatch.chdir(w.base)
    ok, reason = _verify(w)
    proc = subprocess.run(
        [sys.executable, str(TOOL), str(w.note), "--config", str(w.config)],
        capture_output=True,
        cwd=w.base,
        env=_clean_env(),
        timeout=TIMEOUT,
        check=False,
    )
    out = proc.stdout.decode("ascii", "replace").strip()
    leaked = _leaks(w, out + proc.stderr.decode("utf-8", "replace"))
    assert reason == "config-root-not-absolute"
    assert ok is False
    assert out == "config-root-not-absolute"
    assert leaked is False


# --- the CLI -----------------------------------------------------------------


def test_the_cli_exits_zero_and_prints_verified(world: World) -> None:
    proc = _cli(world)
    out = proc.stdout.decode("ascii", "replace").strip()
    code = proc.returncode
    lines = out.splitlines()
    assert lines == ["verified", NOTE_SHA256]
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
    lines = out.splitlines()
    assert lines == ["verified", NOTE_SHA256]
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
    binds_digest = "SHA-256 hex" in text and "second line" in text
    assert names_tool is True
    assert names_function is True
    assert binds_digest is True
