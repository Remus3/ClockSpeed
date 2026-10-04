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
import shutil
import stat
import subprocess
import sys
import threading
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
    verdict = provenance.verify_main_note(w.note, config_path=w.config, inbox_dir=_inbox(w))
    return bool(verdict.ok), str(verdict.reason)


# --- the passing arm ---------------------------------------------------------


def test_a_matching_tracked_note_passes(world: World) -> None:
    verdict = provenance.verify_main_note(
        world.note, config_path=world.config, inbox_dir=_inbox(world)
    )
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
    verdict = provenance.verify_main_note(
        world.note, config_path=world.config, inbox_dir=_inbox(world)
    )
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
        [
            sys.executable,
            str(TOOL),
            str(w.note),
            "--config",
            str(w.config),
            "--inbox",
            str(_inbox(w)),
        ],
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
    verdict = provenance.verify_main_note(
        world.note, config_path=world.config, inbox_dir=_inbox(world)
    )
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
    code = provenance.main(
        [str(world.note), "--config", str(world.config), "--inbox", str(_inbox(world))]
    )
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
        [
            sys.executable,
            str(TOOL),
            str(w.note),
            "--config",
            str(w.config),
            "--inbox",
            str(_inbox(w)),
        ],
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


# --- CS-1232: a file inside a MAIN kit bundle directory ----------------------
#
# MAIN's outbox mirrors a bundle as ``<outbox>/<bundle-dir>/<file>``, and the
# inbox holds it as ``moon_sync_inbox/<bundle-dir>/<file>``. The tool knows THIS
# tree's inbox (``inbox_dir``, injected here as ``config_path`` is) and places
# the RESOLVED note against the RESOLVED inbox - never the note's spelling.

#: The bundle directory's name, on both sides.
BUNDLE_DIR: Final = "cs1232-kit-v1"

#: A file inside the bundle.
BUNDLE_FILE: Final = "LICENSE"

#: The bundle file's bytes - distinct from NOTE_BYTES so a top-level twin can
#: be told apart.
BUNDLE_BYTES: Final = b"synthetic licence text for the CS-1232 arms\n"

#: The SHA-256 hex a verified bundle verdict must carry.
BUNDLE_SHA256: Final = hashlib.sha256(BUNDLE_BYTES).hexdigest()

#: The fixed refusal for a bundle path the check will not interpret.
_BUNDLE_REFUSED: Final = "bundle-path-refused"

#: The bundle file's path relative to MAIN's root.
_BUNDLE_REL: Final = "moon_sync_outbox/" + BUNDLE_DIR + "/" + BUNDLE_FILE


def _inbox(w: World) -> Path:
    """This tree's inbox in ``w`` - the fixture's note sits directly in it."""
    return w.base / "cs1227_this" / "moon_sync_inbox"


def _verify_in(w: World, note: Path | None = None) -> tuple[bool, str, str]:
    """Run the check with the inbox injected; reduce the verdict to scalars."""
    verdict = provenance.verify_main_note(
        w.note if note is None else note, config_path=w.config, inbox_dir=_inbox(w)
    )
    return bool(verdict.ok), str(verdict.reason), str(verdict.digest)


def _cli_in(w: World, note: Path | str | None = None) -> subprocess.CompletedProcess[bytes]:
    """Run the CLI over ``w`` with the inbox injected."""
    target = str(w.note if note is None else note)
    return subprocess.run(
        [
            sys.executable,
            str(TOOL),
            target,
            "--config",
            str(w.config),
            "--inbox",
            str(_inbox(w)),
        ],
        capture_output=True,
        env=_clean_env(),
        timeout=TIMEOUT,
        check=False,
    )


@pytest.fixture
def bundle_world(world: World) -> World:
    """``world`` plus a committed bundle file in MAIN and its inbox twin."""
    outbox_bundle = world.main_root / "moon_sync_outbox" / BUNDLE_DIR
    outbox_bundle.mkdir()
    (outbox_bundle / BUNDLE_FILE).write_bytes(BUNDLE_BYTES)
    _git(world.main_root, "add", "-A")
    _git(world.main_root, "commit", "-q", "-m", "bundle")
    inbox_bundle = _inbox(world) / BUNDLE_DIR
    inbox_bundle.mkdir()
    world.note = inbox_bundle / BUNDLE_FILE
    world.note.write_bytes(BUNDLE_BYTES)
    return world


def _bundle_outbox_file(w: World) -> Path:
    return w.main_root / "moon_sync_outbox" / BUNDLE_DIR / BUNDLE_FILE


def test_a_bundle_file_verifies_by_its_bundle_relative_path(bundle_world: World) -> None:
    ok, reason, digest = _verify_in(bundle_world)
    assert reason == "verified"
    assert ok is True
    assert digest == BUNDLE_SHA256


def test_the_cli_verifies_a_bundle_file(bundle_world: World) -> None:
    proc = _cli_in(bundle_world)
    lines = proc.stdout.decode("ascii", "replace").strip().splitlines()
    code = proc.returncode
    assert lines == ["verified", BUNDLE_SHA256]
    assert code == 0


def test_the_default_inbox_is_this_trees_inbox() -> None:
    default = provenance.DEFAULT_INBOX
    rel = default.relative_to(REPO_ROOT).as_posix()
    assert rel == "moon_sync_inbox"


def _bundle_top_level_twin_only(w: World) -> None:
    # The bundle copy is gone from MAIN; a TOP-LEVEL file of the same name and
    # bytes remains. Looking the note up by bare name would verify it.
    (w.main_root / "moon_sync_outbox" / BUNDLE_FILE).write_bytes(BUNDLE_BYTES)
    _bundle_outbox_file(w).unlink()
    _git(w.main_root, "add", "-A")
    _git(w.main_root, "commit", "-q", "-m", "flatten")


def _bundle_byte_different(w: World) -> None:
    w.note.write_bytes(BUNDLE_BYTES + b"tampered\n")


def _bundle_untracked(w: World) -> None:
    other = "cs1232-untracked.txt"
    (w.main_root / "moon_sync_outbox" / BUNDLE_DIR / other).write_bytes(BUNDLE_BYTES)
    w.note = w.note.with_name(other)
    w.note.write_bytes(BUNDLE_BYTES)


def _bundle_modified(w: World) -> None:
    changed = BUNDLE_BYTES + b"edited after commit\n"
    _bundle_outbox_file(w).write_bytes(changed)
    w.note.write_bytes(changed)


def _bundle_staged_edit_then_restored(w: World) -> None:
    _bundle_outbox_file(w).write_bytes(_EDITED)
    _git(w.main_root, "add", "--", _BUNDLE_REL)
    _bundle_outbox_file(w).write_bytes(BUNDLE_BYTES)


def _bundle_skip_worktree(w: World) -> None:
    _git(w.main_root, "update-index", "--skip-worktree", "--", _BUNDLE_REL)
    _bundle_outbox_file(w).write_bytes(_EDITED)
    w.note.write_bytes(_EDITED)


def _bundle_replaced_blob(w: World) -> None:
    original = _git(w.main_root, "rev-parse", "HEAD:" + _BUNDLE_REL)
    _git(w.main_root, "replace", original, _evil_blob(w))
    _bundle_outbox_file(w).write_bytes(_EVIL)
    w.note.write_bytes(_EVIL)


def _bundle_outbox_absent(w: World) -> None:
    _bundle_outbox_file(w).unlink()
    _git(w.main_root, "commit", "-q", "-a", "-m", "drop")


def _bundle_note_absent(w: World) -> None:
    w.note.unlink()


BUNDLE_REFUSALS: Final[dict[str, tuple[Callable[[World], None], str]]] = {
    "top_level_twin_only": (_bundle_top_level_twin_only, "outbox-file-absent"),
    "byte_different": (_bundle_byte_different, "digest-mismatch"),
    "untracked": (_bundle_untracked, "untracked"),
    "modified": (_bundle_modified, _DIFFERS),
    "staged_edit_then_restored": (_bundle_staged_edit_then_restored, "modified"),
    "skip_worktree": (_bundle_skip_worktree, _DIFFERS),
    "replaced_blob": (_bundle_replaced_blob, _DIFFERS),
    "outbox_absent": (_bundle_outbox_absent, "outbox-file-absent"),
    "note_absent": (_bundle_note_absent, "note-unreadable"),
}


@pytest.mark.parametrize("case", sorted(BUNDLE_REFUSALS))
def test_each_bundle_refusal_names_its_reason(bundle_world: World, case: str) -> None:
    plant, expected = BUNDLE_REFUSALS[case]
    plant(bundle_world)
    ok, reason, digest = _verify_in(bundle_world)
    proc = _cli_in(bundle_world)
    rendered = proc.stdout.decode("utf-8", "replace") + proc.stderr.decode("utf-8", "replace")
    leaked = _leaks(bundle_world, rendered + reason)
    cli_reason = proc.stdout.decode("ascii", "replace").strip() == expected
    assert reason == expected
    assert ok is False
    assert digest == ""
    assert leaked is False
    assert cli_reason is True


def _make_dir_link(link: Path, target: Path) -> bool:
    """Make ``link`` a directory symlink (or, on Windows, a junction) to ``target``."""
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        if sys.platform != "win32":
            return False
        import _winapi  # noqa: PLC0415 - Windows-only fallback

        try:
            _winapi.CreateJunction(str(target), str(link))
        except OSError:
            return False
    return True


def test_an_inbox_bundle_link_leading_outside_is_refused(bundle_world: World) -> None:
    # The inbox entry is a link to a bundle OUTSIDE the inbox: spelled inside,
    # resolved outside - refused (round 4; round 3 sent it to the bare name).
    w = bundle_world
    elsewhere = w.base / "cs1232_elsewhere"
    w.note.parent.rename(elsewhere)
    made = _make_dir_link(_inbox(w) / BUNDLE_DIR, elsewhere)
    if not made:
        pytest.skip("this platform cannot create a directory link here")
    readable = w.note.read_bytes() == BUNDLE_BYTES
    ok, reason, _digest = _verify_in(w)
    assert readable is True
    assert reason == _BUNDLE_REFUSED
    assert ok is False


def test_a_symlinked_outbox_bundle_dir_is_refused(bundle_world: World) -> None:
    # MAIN's outbox bundle dir replaced by a link to a copy: the file read must
    # not follow the link, whatever git's index still records for the path.
    w = bundle_world
    outbox_bundle = w.main_root / "moon_sync_outbox" / BUNDLE_DIR
    elsewhere = w.base / "cs1232_outbox_elsewhere"
    outbox_bundle.rename(elsewhere)
    made = _make_dir_link(outbox_bundle, elsewhere)
    if not made:
        pytest.skip("this platform cannot create a directory link here")
    readable = (outbox_bundle / BUNDLE_FILE).read_bytes() == BUNDLE_BYTES
    ok, reason, _digest = _verify_in(w)
    assert readable is True
    assert reason == "outbox-file-absent"
    assert ok is False


def test_a_deeper_nesting_is_refused(bundle_world: World) -> None:
    w = bundle_world
    deep = _inbox(w) / BUNDLE_DIR / "inner"
    deep.mkdir()
    (deep / BUNDLE_FILE).write_bytes(BUNDLE_BYTES)
    ok, reason, _digest = _verify_in(w, deep / BUNDLE_FILE)
    proc = _cli_in(w, deep / BUNDLE_FILE)
    out = proc.stdout.decode("ascii", "replace").strip()
    leaked = _leaks(w, out + proc.stderr.decode("utf-8", "replace"))
    assert reason == _BUNDLE_REFUSED
    assert ok is False
    assert out == _BUNDLE_REFUSED
    assert leaked is False


def test_the_inbox_itself_is_refused(bundle_world: World) -> None:
    ok, reason, _digest = _verify_in(bundle_world, _inbox(bundle_world))
    assert reason == _BUNDLE_REFUSED
    assert ok is False


@pytest.mark.parametrize(
    "parts",
    [
        ("a:b", BUNDLE_FILE),
        ("a\\b", BUNDLE_FILE),
        ("a\x00b", BUNDLE_FILE),
        ("a\nb", BUNDLE_FILE),
        ("a*b", BUNDLE_FILE),
        (BUNDLE_DIR, "LICENSE."),
        ("..", BUNDLE_FILE),
        (".", BUNDLE_FILE),
        ("", BUNDLE_FILE),
        ("moon_sync_inbox", BUNDLE_FILE),
        ("MOON_SYNC_OUTBOX", BUNDLE_FILE),
        (BUNDLE_DIR, "Moon_Sync_Inbox"),
        (BUNDLE_DIR, "moon_sync_outbox"),
        (BUNDLE_DIR, "inner", BUNDLE_FILE),
        (),
    ],
    ids=[
        "colon",
        "backslash",
        "nul",
        "newline",
        "star",
        "trailing_dot",
        "dotdot",
        "dot",
        "empty",
        "inbox_bundle",
        "outbox_bundle",
        "inbox_file",
        "outbox_file",
        "deeper",
        "none",
    ],
)
def test_inbox_rel_refuses_a_shape_it_will_not_interpret(parts: tuple[str, ...]) -> None:
    # Unrepresentable on some filesystems, so the arm asks the pure mapping.
    parsed = provenance.inbox_rel(parts)
    refused = parsed == _BUNDLE_REFUSED
    assert refused is True


def test_inbox_rel_maps_each_accepted_shape() -> None:
    top = provenance.inbox_rel((NOTE_NAME,))
    bundle = provenance.inbox_rel((BUNDLE_DIR, BUNDLE_FILE))
    assert top == (NOTE_NAME, "")
    assert bundle == (BUNDLE_DIR + "/" + BUNDLE_FILE, BUNDLE_DIR)


def test_the_bundle_refusal_is_in_the_closed_set() -> None:
    member = _BUNDLE_REFUSED in provenance.REASONS
    constant = provenance.BUNDLE_PATH_REFUSED == _BUNDLE_REFUSED
    assert member is True
    assert constant is True


# --- CS-1232 rounds 2 and 3: a reserved name, or a spelling of the inbox -----

#: A second outbox file, committed both top-level and inside the bundle.
_RUN: Final = "run.md"
_RUN_BYTES: Final = b"synthetic run note for the CS-1232 round 2 arms\n"

#: Inbox-relative spellings that must be refused, each naming a reserved name.
_TWICE: Final = {
    "inbox_bundle_then_kit": "moon_sync_inbox/" + BUNDLE_DIR + "/" + _RUN,
    "inbox_as_bundle": "moon_sync_inbox/" + _RUN,
    "inbox_as_bundle_upper": "MOON_SYNC_INBOX/" + _RUN,
    "outbox_as_bundle": "moon_sync_outbox/" + _RUN,
    "outbox_as_bundle_upper": "MOON_SYNC_OUTBOX/" + _RUN,
    "inbox_as_file": BUNDLE_DIR + "/moon_sync_inbox",
    "outbox_as_file": BUNDLE_DIR + "/Moon_Sync_Outbox",
}


@pytest.fixture
def twice_world(bundle_world: World) -> World:
    """MAIN commits ``run.md`` top-level and in the bundle; the inbox holds each spelling.

    Every spelling of :data:`_TWICE` carries the matching bytes, so only the path
    rule can refuse it.
    """
    w = bundle_world
    _git(w.main_root, "config", "core.ignorecase", "true")
    outbox = w.main_root / "moon_sync_outbox"
    (outbox / _RUN).write_bytes(_RUN_BYTES)
    (outbox / BUNDLE_DIR / _RUN).write_bytes(_RUN_BYTES)
    for reserved in ("moon_sync_inbox", "Moon_Sync_Outbox"):
        (outbox / BUNDLE_DIR / reserved).write_bytes(_RUN_BYTES)
    _git(w.main_root, "add", "-A")
    _git(w.main_root, "commit", "-q", "-m", "run")
    for rel in _TWICE.values():
        target = _inbox(w).joinpath(*rel.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_RUN_BYTES)
    return w


@pytest.mark.parametrize("case", sorted(_TWICE))
def test_a_path_naming_a_reserved_dir_below_the_inbox_is_refused(
    twice_world: World, case: str
) -> None:
    w = twice_world
    note = _inbox(w).joinpath(*_TWICE[case].split("/"))
    ok, reason, _digest = _verify_in(w, note)
    proc = _cli_in(w, note)
    out = proc.stdout.decode("ascii", "replace").strip()
    leaked = _leaks(w, out + proc.stderr.decode("utf-8", "replace") + reason)
    assert reason == _BUNDLE_REFUSED
    assert ok is False
    assert out == _BUNDLE_REFUSED
    assert leaked is False


def test_the_twice_world_controls_still_verify(twice_world: World) -> None:
    # Anti-vacuity: the committed run.md files verify through their honest
    # spellings, so a refusal above is the path rule and not a broken fixture.
    w = twice_world
    inbox = _inbox(w)
    (inbox / _RUN).write_bytes(_RUN_BYTES)
    (inbox / BUNDLE_DIR / _RUN).write_bytes(_RUN_BYTES)
    _ok, top_reason, _d = _verify_in(w, inbox / _RUN)
    _ok2, bundled_reason, _d2 = _verify_in(w, inbox / BUNDLE_DIR / _RUN)
    assert top_reason == "verified"
    assert bundled_reason == "verified"


# Round 3 - the spelling of the path must not decide placement. MAIN commits a
# top-level LICENSE "top" and a bundle LICENSE "bund"; the inbox bundle file
# carries "top". Placed as a bundle file it is a digest mismatch; looked up by
# bare name it would wrongly verify against the top-level file.

_TOP: Final = b"top\n"
_BUND: Final = b"bund\n"


@pytest.fixture
def alias_world(bundle_world: World) -> World:
    w = bundle_world
    (w.main_root / "moon_sync_outbox" / BUNDLE_FILE).write_bytes(_TOP)
    _bundle_outbox_file(w).write_bytes(_BUND)
    _git(w.main_root, "add", "-A")
    _git(w.main_root, "commit", "-q", "-m", "alias")
    w.note.write_bytes(_TOP)
    return w


def _assert_mismatch(w: World, note: Path) -> None:
    # Control first: the spelling really does reach the inbox bundle file.
    reaches = note.read_bytes() == _TOP
    ok, reason, _digest = _verify_in(w, note)
    proc = _cli_in(w, note)
    out = proc.stdout.decode("ascii", "replace").strip()
    leaked = _leaks(w, out + proc.stderr.decode("utf-8", "replace") + reason)
    assert reaches is True
    assert reason == "digest-mismatch"
    assert ok is False
    assert out == "digest-mismatch"
    assert leaked is False


def test_the_alias_world_honest_spelling_mismatches(alias_world: World) -> None:
    _assert_mismatch(alias_world, alias_world.note)


def test_an_8dot3_inbox_spelling_is_placed_by_the_resolved_inbox(alias_world: World) -> None:
    w = alias_world
    inbox = _inbox(w)
    short = _short_form(inbox)
    if short is None or Path(short).name.lower() == inbox.name.lower():
        pytest.skip("no 8.3 short name on this platform or volume")
    # Control: the short spelling is a DIFFERENT name for the SAME directory.
    same = Path(short).resolve(strict=True) == inbox.resolve(strict=True)
    assert same is True
    _assert_mismatch(w, Path(short) / BUNDLE_DIR / BUNDLE_FILE)


def test_a_trailing_dot_inbox_spelling_is_placed_by_the_resolved_inbox(
    alias_world: World,
) -> None:
    if sys.platform != "win32":
        pytest.skip("a trailing dot names a different directory off Windows")
    w = alias_world
    inbox = _inbox(w)
    _assert_mismatch(w, Path(str(inbox) + ".") / BUNDLE_DIR / BUNDLE_FILE)


def test_a_linked_alias_of_the_inbox_is_placed_by_the_resolved_inbox(
    alias_world: World,
) -> None:
    w = alias_world
    alias = w.base / "cs1232_alias"
    made = _make_dir_link(alias, _inbox(w))
    if not made:
        pytest.skip("this platform cannot create a directory link here")
    (w.base / "cs1232_sub").mkdir()
    spelled = w.base / "cs1232_sub" / ".." / "cs1232_alias" / BUNDLE_DIR / BUNDLE_FILE
    _assert_mismatch(w, spelled)


@pytest.mark.parametrize("hop", ["dot", "dotdot"])
def test_a_top_level_note_spelled_with_a_hop_still_verifies(world: World, hop: str) -> None:
    # Regression against the pre-CS-1232 tool: these spellings verified there.
    w = world
    inbox = _inbox(w)
    (inbox / "cs1232_hop").mkdir()
    middle = "." if hop == "dot" else "cs1232_hop" + os.sep + ".."
    raw = str(inbox) + os.sep + middle + os.sep + NOTE_NAME
    ok, reason, digest = _verify_in(w, Path(raw))
    proc = _cli_in(w, raw)
    lines = proc.stdout.decode("ascii", "replace").strip().splitlines()
    assert reason == "verified"
    assert ok is True
    assert digest == NOTE_SHA256
    assert lines == ["verified", NOTE_SHA256]


def test_an_inbox_injected_under_an_alias_spelling_is_resolved(alias_world: World) -> None:
    # The INBOX side of the same rule: the injected inbox is spelled with a hop,
    # the note canonically. Only resolving the inbox places the note in it.
    w = alias_world
    (w.base / "cs1232_sub").mkdir()
    hopped = w.base / "cs1232_sub" / ".." / "cs1227_this" / "moon_sync_inbox"
    verdict = provenance.verify_main_note(w.note, config_path=w.config, inbox_dir=hopped)
    reason = str(verdict.reason)
    ok = bool(verdict.ok)
    assert reason == "digest-mismatch"
    assert ok is False


# Round 4 - a note reached through a link, and a note that moves under the read.


def _commit_outbox(w: World, files: dict[str, bytes]) -> None:
    """Commit ``files`` (outbox-relative POSIX paths) into MAIN's outbox."""
    for rel, data in files.items():
        target = (w.main_root / "moon_sync_outbox").joinpath(*rel.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    _git(w.main_root, "add", "-A")
    _git(w.main_root, "commit", "-q", "-m", "round4")


def _refused_quietly(w: World, note: Path) -> tuple[str, str, bool]:
    """The API reason, the CLI line, and whether either rendered a path."""
    _ok, reason, _digest = _verify_in(w, note)
    proc = _cli_in(w, note)
    out = proc.stdout.decode("ascii", "replace").strip()
    leaked = _leaks(w, out + proc.stderr.decode("utf-8", "replace") + reason)
    return reason, out, leaked


def test_a_bundle_file_linking_to_a_top_level_note_is_refused(bundle_world: World) -> None:
    # Repro (a): inbox/<b>/SYM -> inbox/LICENSE. Resolved, it is the top-level
    # note, whose bare name verifies against MAIN's top-level LICENSE.
    w = bundle_world
    _commit_outbox(w, {BUNDLE_FILE: _TOP, BUNDLE_DIR + "/SYM": b"bsym\n"})
    (_inbox(w) / BUNDLE_FILE).write_bytes(_TOP)
    sym = _inbox(w) / BUNDLE_DIR / "SYM"
    try:
        sym.symlink_to(_inbox(w) / BUNDLE_FILE)
    except OSError:
        pytest.skip("this platform cannot create a file symlink here")
    reaches = sym.read_bytes() == _TOP
    reason, out, leaked = _refused_quietly(w, sym)
    assert reaches is True
    assert reason == _BUNDLE_REFUSED
    assert out == _BUNDLE_REFUSED
    assert leaked is False


def test_a_bundle_dir_linking_outside_the_inbox_is_refused(bundle_world: World) -> None:
    # Repro (b): inbox/jb -> an OUTSIDE dir holding LICENSE "top". Resolved, it
    # lies outside the inbox, whose bare-name fallback verifies it.
    w = bundle_world
    _commit_outbox(w, {BUNDLE_FILE: _TOP, "jb/" + BUNDLE_FILE: b"jbund\n"})
    outside = w.base / "cs1232_outside"
    outside.mkdir()
    (outside / BUNDLE_FILE).write_bytes(_TOP)
    made = _make_dir_link(_inbox(w) / "jb", outside)
    if not made:
        pytest.skip("this platform cannot create a directory link here")
    note = _inbox(w) / "jb" / BUNDLE_FILE
    reaches = note.read_bytes() == _TOP
    reason, out, leaked = _refused_quietly(w, note)
    assert reaches is True
    assert reason == _BUNDLE_REFUSED
    assert out == _BUNDLE_REFUSED
    assert leaked is False


def test_a_linked_bundle_dir_is_refused_even_where_placement_agrees(
    bundle_world: World,
) -> None:
    # outside/<b> is a link to inbox/<b>: the resolved placement is the honest
    # bundle file, and the spelling's tail agrees - only the link rule refuses.
    w = bundle_world
    other = w.base / "cs1232_other"
    other.mkdir()
    made = _make_dir_link(other / BUNDLE_DIR, _inbox(w) / BUNDLE_DIR)
    if not made:
        pytest.skip("this platform cannot create a directory link here")
    note = other / BUNDLE_DIR / BUNDLE_FILE
    reaches = note.read_bytes() == BUNDLE_BYTES
    reason, out, leaked = _refused_quietly(w, note)
    assert reaches is True
    assert reason == _BUNDLE_REFUSED
    assert out == _BUNDLE_REFUSED
    assert leaked is False


def test_a_note_file_that_is_a_link_is_refused_even_where_placement_agrees(
    world: World,
) -> None:
    w = world
    other = w.base / "cs1232_other_file"
    other.mkdir()
    link = other / NOTE_NAME
    try:
        link.symlink_to(_inbox(w) / NOTE_NAME)
    except OSError:
        pytest.skip("this platform cannot create a file symlink here")
    reaches = link.read_bytes() == NOTE_BYTES
    reason, out, leaked = _refused_quietly(w, link)
    assert reaches is True
    assert reason == _BUNDLE_REFUSED
    assert out == _BUNDLE_REFUSED
    assert leaked is False


@pytest.mark.parametrize("tail", [".", " ", ". "], ids=["dot", "space", "dot_space"])
def test_a_trailing_dot_or_space_spelling_inside_the_inbox_is_refused(
    world: World, tail: str
) -> None:
    # Parity, decided: inside the inbox a spelling Windows strips is refused,
    # since it names the note by a name its own directory does not hold.
    if sys.platform != "win32":
        pytest.skip("a trailing dot or space names a different file off Windows")
    w = world
    spelled = Path(str(_inbox(w) / NOTE_NAME) + tail)
    reaches = spelled.read_bytes() == NOTE_BYTES
    reason, out, leaked = _refused_quietly(w, spelled)
    assert reaches is True
    assert reason == _BUNDLE_REFUSED
    assert out == _BUNDLE_REFUSED
    assert leaked is False


def test_a_trailing_dot_spelling_outside_the_inbox_keeps_its_old_answer(world: World) -> None:
    # Parity, decided: outside the inbox nothing changed - the bare name as
    # spelled is looked up, and MAIN tracks no such name.
    if sys.platform != "win32":
        pytest.skip("a trailing dot names a different file off Windows")
    w = world
    elsewhere = w.base / "cs1232_elsewhere_dot"
    elsewhere.mkdir()
    (elsewhere / NOTE_NAME).write_bytes(NOTE_BYTES)
    ok, reason, _digest = _verify_in(w, Path(str(elsewhere / NOTE_NAME) + "."))
    assert reason == "untracked"
    assert ok is False


def test_the_note_is_read_once_through_its_resolved_path(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A recording spy: the bytes hashed are read from the RESOLVED path, by one
    # open - not from the spelling the caller passed.
    w = world
    (_inbox(w) / "cs1232_hop").mkdir()
    spelled = _inbox(w) / "cs1232_hop" / ".." / NOTE_NAME
    resolved = (_inbox(w) / NOTE_NAME).resolve(strict=True)
    original = provenance.read_note
    seen: list[Path] = []

    def spy(path: Path) -> object:
        seen.append(Path(path))
        return original(path)

    monkeypatch.setattr(provenance, "read_note", spy)
    ok, reason, _digest = _verify_in(w, spelled)
    reads = len(seen)
    through_resolved = reads == 1 and seen[0] == resolved
    assert reason == "verified"
    assert ok is True
    assert through_resolved is True


def test_a_note_replaced_under_the_read_is_refused(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The note is swapped for a new file of the SAME bytes right after the one
    # open: the bytes hashed are no longer the file placed, so it is refused.
    w = world
    original = provenance.read_note

    def swap(path: Path) -> object:
        result = original(path)
        target = _inbox(w) / NOTE_NAME
        target.unlink()
        target.write_bytes(NOTE_BYTES)
        return result

    monkeypatch.setattr(provenance, "read_note", swap)
    ok, reason, _digest = _verify_in(w)
    assert reason == "note-unreadable"
    assert ok is False


@pytest.mark.parametrize("spelled_via", ["alias", "canonical"])
def test_a_lexical_inbox_is_either_spelling_of_it(bundle_world: World, spelled_via: str) -> None:
    # The inbox is injected as an ALIAS (a link to the real inbox). A note under
    # inbox/jb, where jb links OUTSIDE, must be refused whether the note is
    # spelled through the alias (inside the inbox as given) or canonically
    # (inside the inbox as resolved) - each spelling needs its own root.
    w = bundle_world
    _commit_outbox(w, {BUNDLE_FILE: _TOP, "jb/" + BUNDLE_FILE: b"jbund\n"})
    outside = w.base / "cs1232_outside_root"
    outside.mkdir()
    (outside / BUNDLE_FILE).write_bytes(_TOP)
    alias = w.base / "cs1232_inbox_alias"
    made = _make_dir_link(_inbox(w) / "jb", outside) and _make_dir_link(alias, _inbox(w))
    if not made:
        pytest.skip("this platform cannot create a directory link here")
    root = alias if spelled_via == "alias" else _inbox(w)
    note = root / "jb" / BUNDLE_FILE
    reaches = note.read_bytes() == _TOP
    verdict = provenance.verify_main_note(note, config_path=w.config, inbox_dir=alias)
    reason = str(verdict.reason)
    assert reaches is True
    assert reason == _BUNDLE_REFUSED


@pytest.mark.skipif(os.name != "nt", reason="junctions exist only on Windows")
def test_a_junctioned_bundle_dir_is_refused_even_where_placement_agrees(
    bundle_world: World,
) -> None:
    # The reparse-point arm: a JUNCTION, which is not a symlink to lstat, must
    # be refused as one.
    import _winapi  # noqa: PLC0415 - Windows-only

    w = bundle_world
    other = w.base / "cs1232_junction_other"
    other.mkdir()
    _winapi.CreateJunction(str(_inbox(w) / BUNDLE_DIR), str(other / BUNDLE_DIR))
    note = other / BUNDLE_DIR / BUNDLE_FILE
    is_symlink = (other / BUNDLE_DIR).is_symlink()
    reaches = note.read_bytes() == BUNDLE_BYTES
    reason, out, leaked = _refused_quietly(w, note)
    assert is_symlink is False
    assert reaches is True
    assert reason == _BUNDLE_REFUSED
    assert out == _BUNDLE_REFUSED
    assert leaked is False


# Round 5 - the SPELLED placement must equal the resolved one, whole: same
# length, same names, and no link anywhere below the inbox in the spelling.

_XBUND: Final = b"xbund\n"
_DEEP: Final = b"deep\n"


@pytest.fixture
def loop_world(bundle_world: World) -> World:
    """MAIN commits four LICENSE files; inbox/x links back at the inbox itself.

    MAIN: LICENSE, x/LICENSE, x/b/LICENSE and b/LICENSE. The inbox holds
    LICENSE "top" and b/LICENSE "deep".
    """
    w = bundle_world
    _commit_outbox(
        w,
        {
            BUNDLE_FILE: _TOP,
            "x/" + BUNDLE_FILE: _XBUND,
            "x/b/" + BUNDLE_FILE: _DEEP,
            "b/" + BUNDLE_FILE: _DEEP,
        },
    )
    (_inbox(w) / BUNDLE_FILE).write_bytes(_TOP)
    (_inbox(w) / "b").mkdir()
    (_inbox(w) / "b" / BUNDLE_FILE).write_bytes(_DEEP)
    made = _make_dir_link(_inbox(w) / "x", _inbox(w))
    if not made:
        pytest.skip("this platform cannot create a directory link here")
    return w


def test_a_child_aliasing_the_inbox_does_not_bind_to_the_top_level(loop_world: World) -> None:
    # inbox/x/LICENSE resolves to inbox/LICENSE: the spelling is two deep, the
    # resolved placement one deep - they disagree, so it is refused.
    w = loop_world
    note = _inbox(w) / "x" / BUNDLE_FILE
    reaches = note.read_bytes() == _TOP
    reason, out, leaked = _refused_quietly(w, note)
    assert reaches is True
    assert reason == _BUNDLE_REFUSED
    assert out == _BUNDLE_REFUSED
    assert leaked is False


def test_a_three_deep_spelling_through_an_inbox_alias_is_refused(loop_world: World) -> None:
    # inbox/x/b/LICENSE resolves to inbox/b/LICENSE - a bundle file reached by a
    # spelling three deep.
    w = loop_world
    note = _inbox(w) / "x" / "b" / BUNDLE_FILE
    reaches = note.read_bytes() == _DEEP
    reason, out, leaked = _refused_quietly(w, note)
    assert reaches is True
    assert reason == _BUNDLE_REFUSED
    assert out == _BUNDLE_REFUSED
    assert leaked is False


def test_the_loop_world_honest_spellings_still_verify(loop_world: World) -> None:
    # Anti-vacuity: the same files spelled without the alias verify, so the
    # refusals above are the placement rule and not a broken fixture.
    w = loop_world
    _ok, top, _d = _verify_in(w, _inbox(w) / BUNDLE_FILE)
    _ok2, bundled, _d2 = _verify_in(w, _inbox(w) / "b" / BUNDLE_FILE)
    assert top == "verified"
    assert bundled == "verified"


@pytest.mark.parametrize(
    ("link", "target", "spelled"),
    [
        (("y",), (), ("y", "b", BUNDLE_FILE)),
        (("y",), ("b",), ("y", BUNDLE_FILE)),
        (("y",), None, ("y", BUNDLE_FILE)),
        (("b", "back"), (), ("b", "back", BUNDLE_FILE)),
        (("b", "same"), ("b",), ("b", "same", BUNDLE_FILE)),
        (("b", "out"), None, ("b", "out", BUNDLE_FILE)),
    ],
    ids=[
        "depth1_aliases_inbox",
        "depth1_aliases_bundle",
        "depth1_aliases_outside",
        "depth2_aliases_inbox",
        "depth2_aliases_bundle",
        "depth2_aliases_outside",
    ],
)
def test_a_link_at_any_depth_below_the_inbox_is_refused(
    loop_world: World,
    link: tuple[str, ...],
    target: tuple[str, ...] | None,
    spelled: tuple[str, ...],
) -> None:
    # ``target`` is a path under the inbox, or None for a directory outside it
    # holding the same bytes. Every spelling reaches a file whose bytes some
    # MAIN path carries; only the placement rule refuses it.
    w = loop_world
    if target is None:
        aim = w.base / ("cs1232_out_" + "_".join(link))
        aim.mkdir()
        (aim / BUNDLE_FILE).write_bytes(_TOP)
        (aim / "b").mkdir()
        (aim / "b" / BUNDLE_FILE).write_bytes(_DEEP)
    else:
        aim = _inbox(w).joinpath(*target)
    made = _make_dir_link(_inbox(w).joinpath(*link), aim)
    if not made:
        pytest.skip("this platform cannot create a directory link here")
    note = _inbox(w).joinpath(*spelled)
    reaches = note.is_file()
    reason, out, leaked = _refused_quietly(w, note)
    assert reaches is True
    assert reason == _BUNDLE_REFUSED
    assert out == _BUNDLE_REFUSED
    assert leaked is False


def test_a_note_linking_to_its_own_bundle_dir_is_refused(bundle_world: World) -> None:
    # The spelled placement is one longer than the resolved one, and agrees on
    # every shared name - only the length rule refuses it with the right reason.
    w = bundle_world
    made = _make_dir_link(_inbox(w) / BUNDLE_DIR / "c", _inbox(w) / BUNDLE_DIR)
    if not made:
        pytest.skip("this platform cannot create a directory link here")
    reason, out, leaked = _refused_quietly(w, _inbox(w) / BUNDLE_DIR / "c")
    assert reason == _BUNDLE_REFUSED
    assert out == _BUNDLE_REFUSED
    assert leaked is False


def test_every_spelled_component_below_the_inbox_is_lstat_checked(
    bundle_world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    # With whole-placement equality a link below the inbox already changes the
    # resolved placement, so the lstat walk is behaviourally redundant; this
    # recording spy pins it structurally - each spelled component is checked.
    w = bundle_world
    original = provenance.is_link
    seen: list[str] = []

    def spy(path: Path) -> bool:
        seen.append(os.path.normcase(str(path)))
        return bool(original(path))

    monkeypatch.setattr(provenance, "is_link", spy)
    ok, reason, _digest = _verify_in(w)
    want = {os.path.normcase(str(_inbox(w) / BUNDLE_DIR)), os.path.normcase(str(w.note))}
    missing = len(want - set(seen))
    assert reason == "verified"
    assert ok is True
    assert missing == 0


def test_is_link_sees_a_directory_link_and_not_a_plain_dir(tmp_path: Path) -> None:
    plain = tmp_path / "cs1232_plain_dir"
    plain.mkdir()
    link = tmp_path / "cs1232_dir_link"
    made = _make_dir_link(link, plain)
    if not made:
        pytest.skip("this platform cannot create a directory link here")
    link_seen = bool(provenance.is_link(link))
    plain_seen = bool(provenance.is_link(plain))
    assert link_seen is True
    assert plain_seen is False


@pytest.mark.skipif(os.name != "nt", reason="junctions exist only on Windows")
def test_is_link_sees_a_junction(tmp_path: Path) -> None:
    import _winapi  # noqa: PLC0415 - Windows-only

    plain = tmp_path / "cs1232_junction_target"
    plain.mkdir()
    junction = tmp_path / "cs1232_junction"
    _winapi.CreateJunction(str(plain), str(junction))
    not_symlink = junction.is_symlink() is False
    junction_seen = bool(provenance.is_link(junction))
    assert not_symlink is True
    assert junction_seen is True


# Round 6 - placement by FILE IDENTITY. A spelling the resolver keeps in a
# different form (``\\?\`` or an admin-share UNC path) must still be placed as
# the bundle file it is, so MAIN's top-level blob never binds to it.


def test_a_verbatim_prefix_spelling_is_placed_by_identity(alias_world: World) -> None:
    if sys.platform != "win32":
        pytest.skip("the verbatim prefix is a Windows spelling")
    w = alias_world
    spelled = Path("\\\\?\\" + str(w.note))
    _assert_mismatch(w, spelled)


def _admin_share(path: Path) -> Path | None:
    """``path`` spelled through the localhost admin share, or None off Windows."""
    if sys.platform != "win32" or len(path.drive) != 2:  # noqa: PLR2004 - "C:"
        return None
    return Path("\\\\localhost\\" + path.drive[0] + "$" + str(path)[2:])


def test_an_admin_share_spelling_is_placed_by_identity(alias_world: World) -> None:
    w = alias_world
    spelled = _admin_share(w.note)
    if spelled is None:
        pytest.skip("the admin share is a Windows spelling")
    # Control: skip ONLY when the share demonstrably cannot reach the file.
    try:
        reachable = spelled.read_bytes() == _TOP
    except OSError:
        reachable = False
    if not reachable:
        pytest.skip("the localhost admin share is unavailable on this machine")
    _assert_mismatch(w, spelled)


def test_the_opened_file_must_be_the_identified_note(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The note is replaced (same bytes, new file) BEFORE the one open: the file
    # read is not the file identified, so the bytes are not the note's.
    w = world
    original = provenance.read_note

    def swap_first(path: Path) -> object:
        target = _inbox(w) / NOTE_NAME
        target.unlink()
        target.write_bytes(NOTE_BYTES)
        return original(path)

    monkeypatch.setattr(provenance, "read_note", swap_first)
    ok, reason, _digest = _verify_in(w)
    assert reason == "note-unreadable"
    assert ok is False


def test_a_pinned_note_still_verifies(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    # CS-1232 POSIX: off Windows a freed inode number is reissued, so the note
    # is held open across the check. The pin is forced on here so the branch
    # POSIX takes is exercised on every platform: an untouched note verifies.
    monkeypatch.setattr(provenance, "_PIN_NEEDED", True)
    ok, reason, _digest = _verify_in(world)
    assert reason == "verified"
    assert ok is True


def test_a_placed_note_that_cannot_be_pinned_is_refused(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Where a pin is needed and cannot be taken, a placed identity proves
    # nothing about the bytes read, so the note is refused, never verified.
    monkeypatch.setattr(provenance, "_PIN_NEEDED", True)
    monkeypatch.setattr(provenance, "_pin", lambda _note: None)
    ok, reason, _digest = _verify_in(world)
    assert reason == "note-unreadable"
    assert ok is False


def _verify_bounded(w: World, seconds: float = 20.0) -> tuple[bool, str, str]:
    """Run the check on a daemon thread; a hang FAILS the arm instead of the run."""
    out: list[tuple[bool, str, str]] = []
    runner = threading.Thread(target=lambda: out.append(_verify_in(w)), daemon=True)
    runner.start()
    runner.join(seconds)
    hung = runner.is_alive()
    if hung:
        pytest.fail("the check hung on a non-regular note")
    return out[0]


def test_a_non_regular_note_is_never_pinned(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    # The pin opens the note BEFORE placement has seen its kind, so it opens
    # non-blocking and refuses anything but a regular file: a FIFO planted as
    # the note must be refused, never hang the tool. Where os.mkfifo exists a
    # real FIFO replaces the note; elsewhere fstat is made to report one.
    monkeypatch.setattr(provenance, "_PIN_NEEDED", True)
    target = _inbox(world) / NOTE_NAME
    mkfifo = getattr(os, "mkfifo", None)
    if mkfifo is not None:
        target.unlink()
        mkfifo(target)
    else:
        real_fstat = os.fstat

        def fifo_fstat(fd: int) -> os.stat_result:
            got = real_fstat(fd)
            fields = list(got[:10])
            fields[0] = stat.S_IFIFO | 0o644
            return os.stat_result(fields)

        monkeypatch.setattr(os, "fstat", fifo_fstat)
    ok, reason, _digest = _verify_bounded(world)
    assert reason in {"note-unreadable", "bundle-path-refused"}
    assert ok is False


def test_a_pin_on_another_file_is_refused(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    # The pin must hold the PLACED identity: a pin taken on a different file
    # (the note replaced between the pin and the identifying stat) is refused.
    other = world.base / "cs1232_other_pin"
    other.write_bytes(NOTE_BYTES)
    monkeypatch.setattr(provenance, "_PIN_NEEDED", True)
    monkeypatch.setattr(provenance, "_pin", lambda _note: os.open(other, os.O_RDONLY))
    ok, reason, _digest = _verify_in(world)
    assert reason == "note-unreadable"
    assert ok is False


def test_a_note_hardlinked_at_two_inbox_places_is_refused(bundle_world: World) -> None:
    w = bundle_world
    twin = _inbox(w) / BUNDLE_FILE
    try:
        os.link(w.note, twin)
    except OSError:
        pytest.skip("this volume cannot create a hard link here")
    ok, reason, _digest = _verify_in(w)
    assert reason == _BUNDLE_REFUSED
    assert ok is False


def test_a_hardlink_outside_the_inbox_is_placed_as_its_inbox_twin(
    alias_world: World,
) -> None:
    # Identity, not spelling: an outside hard link IS the inbox bundle file.
    w = alias_world
    outside = w.base / "cs1232_hardlink_out"
    outside.mkdir()
    twin = outside / BUNDLE_FILE
    try:
        os.link(w.note, twin)
    except OSError:
        pytest.skip("this volume cannot create a hard link here")
    _assert_mismatch(w, twin)


def test_a_zero_file_index_is_check_failed(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    # A filesystem that reports no file index cannot place by identity at all.
    def no_index(status: os.stat_result) -> tuple[int, int]:
        return int(status.st_dev), 0

    monkeypatch.setattr(provenance, "_identity", no_index)
    ok, reason, _digest = _verify_in(world)
    assert reason == "check-failed"
    assert ok is False


# Round 7 - a census error refuses; every arm names its inbox; parity with the
# pre-CS-1232 tool (41f1835) for a plain top-level note.

#: The fixed refusal for an inbox the census could not finish.
_CENSUS: Final = "census-failed"


def _plant_unstattable(w: World) -> bool:
    """Plant an inbox entry ``zz.`` that scandir lists but lstat cannot reach."""
    try:
        Path("\\\\?\\" + str(_inbox(w).resolve(strict=True) / "zz.")).write_bytes(b"x")
    except OSError:
        return False
    names = {entry.name for entry in os.scandir(_inbox(w))}
    try:
        (_inbox(w) / "zz.").lstat()
    except OSError:
        return "zz." in names
    return False


@pytest.mark.parametrize("twin", [False, True], ids=["plain", "hardlink_twin"])
def test_an_inbox_entry_lstat_cannot_reach_refuses(alias_world: World, twin: bool) -> None:
    if sys.platform != "win32":
        pytest.skip("a trailing-dot entry is only unreachable on Windows")
    w = alias_world
    if twin:
        os.link(w.note, _inbox(w) / BUNDLE_FILE)
    # Control: the honest answer before the plant is the bundle-file mismatch,
    # or with a hard-link twin the two-place refusal.
    _ok, before, _d = _verify_in(w)
    planted = _plant_unstattable(w)
    assert planted is True
    ok, reason, _digest = _verify_in(w)
    proc = _cli_in(w)
    out = proc.stdout.decode("ascii", "replace").strip()
    leaked = _leaks(w, out + proc.stderr.decode("utf-8", "replace") + reason)
    assert before == (_BUNDLE_REFUSED if twin else "digest-mismatch")
    assert reason == _CENSUS
    assert ok is False
    assert out == _CENSUS
    assert leaked is False


def test_a_scandir_error_refuses(bundle_world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*_args: object, **_kwargs: object) -> None:
        raise PermissionError

    monkeypatch.setattr(os, "scandir", refuse)
    ok, reason, _digest = _verify_in(bundle_world)
    assert reason == _CENSUS
    assert ok is False


def test_an_inbox_that_exists_but_will_not_resolve_refuses(
    bundle_world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Only an ABSENT inbox means "no inbox"; any other failure is fail-closed.
    original = Path.resolve
    inbox = _inbox(bundle_world)

    def resolve(self: Path, strict: bool = False) -> Path:
        if self == inbox:
            raise PermissionError
        return original(self, strict=strict)

    monkeypatch.setattr(Path, "resolve", resolve)
    ok, reason, _digest = _verify_in(bundle_world)
    assert reason == _CENSUS
    assert ok is False


def test_an_absent_inbox_refuses_a_plain_note(world: World) -> None:
    # Round 8 ruling: an absent inbox fails closed, even for a note 41f1835
    # verified - declared in the docstring.
    w = world
    verdict = provenance.verify_main_note(
        w.note, config_path=w.config, inbox_dir=w.base / "cs1232_no_inbox"
    )
    reason = str(verdict.reason)
    assert reason == "inbox-absent"


def test_is_link_counts_an_unreadable_path_as_a_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Fail closed: a path whose kind cannot be read is treated as a link.
    target = tmp_path / "cs1232_unreadable"
    target.write_bytes(b"x")
    original = Path.lstat

    def lstat(self: Path) -> os.stat_result:
        if self == target:
            raise PermissionError
        return original(self)

    monkeypatch.setattr(Path, "lstat", lstat)
    unreadable = bool(provenance.is_link(target))
    missing = bool(provenance.is_link(tmp_path / "cs1232_missing"))
    assert unreadable is True
    assert missing is False


def test_the_census_failure_is_in_the_closed_set() -> None:
    member = _CENSUS in provenance.REASONS
    constant = provenance.CENSUS_FAILED == _CENSUS
    assert member is True
    assert constant is True


# Parity: a plain top-level note spelled plainly in the inbox gets 41f1835's
# answer. Each expectation below was MEASURED by running the 41f1835 tool over
# the same synthetic plant, not derived from the current code.

_PARITY_41F1835: Final[dict[str, tuple[Callable[[World], None], str]]] = {
    "verified": (lambda _w: None, "verified"),
    "mismatch": (_byte_different, "digest-mismatch"),
    "untracked": (_untracked, "untracked"),
    "outbox_absent": (_outbox_absent, "outbox-file-absent"),
    "missing_note": (_note_absent, "note-unreadable"),
}


@pytest.mark.parametrize("case", sorted(_PARITY_41F1835))
def test_a_plain_top_level_note_matches_41f1835(world: World, case: str) -> None:
    plant, expected = _PARITY_41F1835[case]
    plant(world)
    _ok, reason, _digest = _verify_in(world)
    assert reason == expected


def test_declared_divergence_a_missing_note_is_unreadable_first(world: World) -> None:
    # 41f1835 answered outbox-file-absent here (measured); the note is now
    # stat-ed before MAIN's outbox is consulted. Declared in the docstring.
    _note_absent(world)
    _outbox_absent(world)
    _ok, reason, _digest = _verify_in(world)
    assert reason == "note-unreadable"


# Test hygiene: every call of the check names its inbox, so no arm's outcome
# depends on the real moon_sync_inbox of whatever checkout runs it.


def _unnamed_inbox_calls(source: str) -> tuple[int, int]:
    """Count (calls of the check, those naming no inbox) in ``source``."""
    import ast  # noqa: PLC0415 - only this guard parses source

    total = 0
    bad = 0
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "verify_main_note":
            total += 1
            bad += not any(k.arg == "inbox_dir" for k in node.keywords)
        if isinstance(node, ast.List):
            texts = {e.value for e in node.elts if isinstance(e, ast.Constant)}
            names_tool = (
                any(isinstance(e, ast.Call) and "TOOL" in ast.dump(e) for e in node.elts)
                or "--config" in texts
            )
            if names_tool:
                total += 1
                bad += "--inbox" not in texts
    return total, bad


#: Fewer calls than this means the guard's parse missed the arms it polices.
_MIN_CHECK_CALLS: Final = 10


def test_every_call_of_the_check_names_its_inbox() -> None:
    total, bad = _unnamed_inbox_calls(Path(__file__).read_text(encoding="ascii"))
    assert total > _MIN_CHECK_CALLS
    assert bad == 0


def test_the_inbox_guard_sees_an_unnamed_call() -> None:
    # Anti-vacuity: the guard fires on each shape it polices.
    api = "provenance.verify_main_note(n, config_path=c)\n"
    cli = "subprocess.run([sys.executable, str(TOOL), n, '--config', c])\n"
    good = "provenance.verify_main_note(n, config_path=c, inbox_dir=i)\n"
    assert _unnamed_inbox_calls(api) == (1, 1)
    assert _unnamed_inbox_calls(cli) == (1, 1)
    assert _unnamed_inbox_calls(good) == (1, 0)


# Round 7 audit - every except clause in the tool fails closed. One arm per
# clause not already pinned above (config_absent, the JSON arms, note_absent,
# the boundary's check-failed, the interrupt, the census and is_link arms).


def test_a_config_that_is_a_directory_is_unparseable(world: World) -> None:
    w = world
    w.config.unlink()
    w.config.mkdir()
    ok, reason = _verify(w)
    assert reason == "config-unparseable"
    assert ok is False


def test_git_that_cannot_run_is_git_failed(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    def no_git(*_args: object, **_kwargs: object) -> None:
        raise OSError

    monkeypatch.setattr(provenance.subprocess, "run", no_git)
    ok, reason = _verify(world)
    assert reason == "git-failed"
    assert ok is False


def test_an_ancestor_link_whose_parent_cannot_be_stat_ed_refuses(
    bundle_world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    w = bundle_world
    original_link = provenance.is_link
    original_stat = Path.stat

    def link(path: Path) -> bool:
        return path == w.note or bool(original_link(path))

    def stat(self: Path, *, follow_symlinks: bool = True) -> os.stat_result:
        if self == w.note.parent:
            raise PermissionError
        return original_stat(self, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(provenance, "is_link", link)
    monkeypatch.setattr(Path, "stat", stat)
    ok, reason, _digest = _verify_in(w)
    assert reason == _BUNDLE_REFUSED
    assert ok is False


def test_a_placed_note_that_will_not_open_is_unreadable(
    bundle_world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = Path.open
    placed = os.path.normcase(str(bundle_world.note.resolve(strict=True)))

    def refuse(self: Path, *args: object, **kwargs: object) -> object:
        if os.path.normcase(str(self)) == placed:
            raise PermissionError
        return original(self, *args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(Path, "open", refuse)
    ok, reason, _digest = _verify_in(bundle_world)
    assert reason == "note-unreadable"
    assert ok is False


def test_a_placed_note_deleted_under_the_read_is_unreadable(
    bundle_world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    w = bundle_world
    original = provenance.read_note

    def delete_after(path: Path) -> object:
        result = original(path)
        w.note.unlink()
        return result

    monkeypatch.setattr(provenance, "read_note", delete_after)
    ok, reason, _digest = _verify_in(w)
    assert reason == "note-unreadable"
    assert ok is False


def test_an_outbox_file_that_will_not_read_is_outbox_unreadable(
    bundle_world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    w = bundle_world
    original = Path.read_bytes

    def refuse(self: Path) -> bytes:
        if self == _bundle_outbox_file(w):
            raise PermissionError
        return original(self)

    monkeypatch.setattr(Path, "read_bytes", refuse)
    ok, reason, _digest = _verify_in(w)
    assert reason == "outbox-unreadable"
    assert ok is False


def test_the_census_records_no_link_entry(loop_world: World) -> None:
    # Structural pin: a link entry is recorded under its own lstat identity and
    # never descended, so skipping it changes no verdict - but the census must
    # still hold none, so no future placement can land on one.
    w = loop_world
    census = provenance.inbox_census(_inbox(w).resolve(strict=True))
    names = {entry.parts[-1] for entries in census.values() for entry in entries if entry.parts}
    holds_link = "x" in names
    holds_bundle = "b" in names
    assert holds_bundle is True
    assert holds_link is False


# Round 8 - an absent inbox is not "no inbox": it refuses, fail-closed.

#: The fixed refusal when this tree's inbox does not exist.
_INBOX_ABSENT: Final = "inbox-absent"


def test_an_absent_default_inbox_refuses_a_bundle_file(
    alias_world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Repro h9: the DEFAULT inbox (derived from the tool's location) is absent
    # - as in any worktree - while the note sits in a populated inbox elsewhere.
    # The bare-name answer would verify the bundle file against MAIN's
    # top-level LICENSE; an absent inbox must refuse instead.
    w = alias_world
    monkeypatch.setattr(provenance, "DEFAULT_INBOX", w.base / "cs1232_absent_default")
    verdict = provenance.verify_main_note(w.note, config_path=w.config, inbox_dir=None)
    reason = str(verdict.reason)
    ok = bool(verdict.ok)
    assert reason == _INBOX_ABSENT
    assert ok is False


def test_an_absent_injected_inbox_refuses_through_the_cli(alias_world: World) -> None:
    w = alias_world
    missing = w.base / "cs1232_absent_inbox"
    proc = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            str(w.note),
            "--config",
            str(w.config),
            "--inbox",
            str(missing),
        ],
        capture_output=True,
        env=_clean_env(),
        timeout=TIMEOUT,
        check=False,
    )
    out = proc.stdout.decode("ascii", "replace").strip()
    code = proc.returncode
    leaked = _leaks(w, out + proc.stderr.decode("utf-8", "replace"))
    assert out == _INBOX_ABSENT
    assert code == 1
    assert leaked is False


def test_the_inbox_absent_refusal_is_in_the_closed_set() -> None:
    member = _INBOX_ABSENT in provenance.REASONS
    constant = provenance.INBOX_ABSENT == _INBOX_ABSENT
    assert member is True
    assert constant is True


#: Everyone, by its well-known SID - no account name is ever named.
_EVERYONE: Final = "*S-1-1-0"


def test_an_unreadable_inbox_subdirectory_refuses(world: World) -> None:
    # The h7 lens: a subdirectory the census cannot list. An icacls deny on
    # Everyone makes it unlistable; the arm skips only when a CONTROL shows the
    # deny did not take.
    if sys.platform != "win32":
        pytest.skip("icacls is a Windows tool")
    w = world
    locked = _inbox(w) / "cs1232_locked"
    locked.mkdir()
    (locked / "inner.md").write_bytes(b"x\n")
    icacls = shutil.which("icacls")
    if icacls is None:
        pytest.skip("icacls is not on PATH")
    deny = [icacls, str(locked), "/deny", _EVERYONE + ":(OI)(CI)(RD)"]
    undo = [icacls, str(locked), "/remove:d", _EVERYONE]
    subprocess.run(deny, capture_output=True, timeout=TIMEOUT, check=False)
    try:
        try:
            with os.scandir(locked) as entries:
                list(entries)
            denied = False
        except PermissionError:
            denied = True
        if not denied:
            pytest.skip("the icacls deny did not take on this volume")
        ok, reason, _digest = _verify_in(w)
    finally:
        subprocess.run(undo, capture_output=True, timeout=TIMEOUT, check=False)
    assert reason == _CENSUS
    assert ok is False
