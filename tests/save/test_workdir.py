"""The work directory: the only writer in the save package, proven read-only at its source.

WHAT THIS MODULE IS FOR. ``clockspeed/save/workdir.py`` holds the single write
in ``clockspeed/save/`` (docs/ARCHITECTURE.md section 1.1, docs/adr/0007
Decision item 6). Everything here exists to make the never-write invariant
(CLAUDE.md non-negotiable 1, memory/never-write-to-the-game.md) a MEASURED
property rather than a reviewed one.

The invariant has two halves and both are covered below:

- **The source is never written.** Proven twice, deliberately by two unrelated
  mechanisms. ``test_the_source_is_untouched_by_the_copy`` compares size,
  ``st_mtime_ns`` and sha256 across the copy; ``st_mtime_ns`` is the field that
  catches an accidental open-for-append, which a size or hash check alone would
  miss on a re-written identical byte. ``test_no_write_intent_event_reaches_the
  _save_root`` installs an audit hook in a child interpreter and watches the
  interpreter's own event stream instead. A single check would be one bug away
  from vacuous; these two fail for different reasons.
- **The destination is never inside the save root or the install.** A copy
  written back into the save directory would violate the invariant just as
  surely as an in-place parse, so ``copy_for_read`` refuses, and the refusal is
  tested against a plain path, a ``..`` traversal and a symlink.

NOTHING HERE TOUCHES THE REAL MACHINE. The ``isolate_from_the_real_machine``
fixture is autouse, so every test in this module runs with all four
``CLOCKSPEED_*`` overrides pointed at a path asserted not to exist. That is
structural rather than per-test on purpose: a test that forgot to isolate
itself would silently read the operator's real save directory on the one
machine where the mistake is invisible - the machine where the game IS
installed, because there it passes.

WHY THE COUNTS IN THE AUDIT TEST MATTER. Asserting only "no writes happened"
passes for a function that does nothing at all. The read-open count is asserted
non-zero in the same test for that reason; it is what proves the hook was
actually watching a function that actually ran.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from clockspeed.data.locate import (
    ENV_ACCOUNT_DIR,
    ENV_GAME_DIR,
    ENV_LOCAL_CONFIG,
    ENV_SAVE_ROOT,
)
from clockspeed.save import workdir
from tests.save import synthetic

# ---------------------------------------------------------------------------
# Paths, derived rather than written down
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
THIS_MODULE = Path(__file__).resolve()

# The path every override points at. Under the repo root rather than under a
# temporary directory so it needs no fixture and is identical in every child,
# and asserted absent below so it can never quietly become real and turn the
# isolation into a no-op. Same device, same reasoning, as
# tests/data/test_phase2_gate.py::ABSENT.
ABSENT = REPO_ROOT / "no-such-path-workdir-suite"

# A synthetic stand-in for the account directory. Ten digits, which is at or
# above clockspeed.data.locate.MIN_ACCOUNT_ID_DIGITS, so redact() treats it the
# way it treats a real one - which is what lets the redaction test below assert
# that these exact characters do NOT survive into a message. It is invented.
PRETEND_ACCOUNT = "1234567890"

_CHILD_TIMEOUT_SECONDS = 300

# Expected counts, named so the assertions read as contracts rather than as
# magic numbers.
EXPECT_NONE = 0
EXPECT_AT_LEAST_ONE = 1

# A write-capable open, found by extracting the MODE argument and testing it,
# rather than by looking for a mode character anywhere inside the call. The
# naive form matches open("data.txt") on the "a" in "data" and reports a read
# as a write; this one cannot, because it only ever inspects the captured mode.
WRITE_MODE_CHARS = frozenset("wax+")
_DOT_OPEN = re.compile(r"""\.open\s*\(\s*(["'])([^"']*)\1""")
_BUILTIN_OPEN = re.compile(r"""(?<![.\w])open\s*\([^,()]*,\s*(["'])([^"']*)\1""")


def write_modes_in(text: str) -> list[str]:
    """Return every file mode in ``text`` that a file could be written through."""
    modes = [
        match.group(2) for pattern in (_DOT_OPEN, _BUILTIN_OPEN) for match in pattern.finditer(text)
    ]
    return [mode for mode in modes if WRITE_MODE_CHARS & set(mode)]


# ---------------------------------------------------------------------------
# Isolation
# ---------------------------------------------------------------------------


def test_the_forced_absent_path_really_is_absent() -> None:
    """If ABSENT ever became real, every isolation assertion below is vacuous."""
    assert not ABSENT.exists(), (
        f"{ABSENT.name} exists, so the no-install overrides resolve to something real"
    )


@pytest.fixture(autouse=True)
def isolate_from_the_real_machine(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point every resolver at nothing, for every test in this module.

    All four overrides, not just the two that name a save location.
    ``CLOCKSPEED_LOCAL_CONFIG`` is the one that is easy to forget and the one
    that matters most: without it, ``locate.local_config()`` reads the
    operator's real ``config/local.json`` and a "pretend" save root quietly
    becomes the real one.
    """
    monkeypatch.setenv(ENV_GAME_DIR, str(ABSENT / "install"))
    monkeypatch.setenv(ENV_SAVE_ROOT, str(ABSENT / "saves"))
    monkeypatch.setenv(ENV_ACCOUNT_DIR, str(ABSENT / "account"))
    monkeypatch.setenv(ENV_LOCAL_CONFIG, str(ABSENT / "local.json"))
    # An operator who has this set in their shell would otherwise change where
    # the default-work-root test looks.
    monkeypatch.delenv(workdir.ENV_WORK_ROOT, raising=False)


# ---------------------------------------------------------------------------
# Fixtures - synthetic bytes and a pretend save root, never a real one
# ---------------------------------------------------------------------------


@pytest.fixture
def save_bytes() -> bytes:
    """A whole synthetic save. Invented bytes, built in-repo, never a real save."""
    return synthetic.build_save()


@pytest.fixture
def pretend_save_root(tmp_path: Path) -> Path:
    """A stand-in save root with an account directory beneath it."""
    root = tmp_path / "pretend_saves"
    (root / PRETEND_ACCOUNT).mkdir(parents=True)
    return root


@pytest.fixture
def pretend_account_dir(pretend_save_root: Path) -> Path:
    """The account directory beneath the pretend save root."""
    return pretend_save_root / PRETEND_ACCOUNT


@pytest.fixture
def pretend_source(pretend_account_dir: Path, save_bytes: bytes) -> Path:
    """A synthetic save sitting where a real one would sit."""
    source = pretend_account_dir / "SyntheticWorld.sav"
    source.write_bytes(save_bytes)
    return source


@pytest.fixture
def work(tmp_path: Path) -> Path:
    """A work root well outside the pretend save root."""
    return tmp_path / "work"


def sha256_of(path: Path) -> str:
    """Hash a file's bytes. Compared instead of length, per the acceptance criteria."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stat_triple(path: Path) -> tuple[int, int, str]:
    """Return (size, st_mtime_ns, sha256) - the three fields asserted unchanged."""
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, sha256_of(path)


# ===========================================================================
# 1. The copy is byte-identical
# ===========================================================================


def test_the_copy_is_byte_identical_to_the_source(pretend_source: Path, work: Path) -> None:
    """sha256 of the copy equals sha256 of the source, and it lands under the work root."""
    copy = workdir.copy_for_read(pretend_source, work_root=work)

    assert copy.is_file(), "copy_for_read returned a path that is not a file"
    assert copy.resolve().is_relative_to(work.resolve()), "the copy landed outside the work root"
    assert sha256_of(copy) == sha256_of(pretend_source), "the copy is not byte-identical"


def test_the_copy_survives_a_body_with_every_byte_value(
    pretend_account_dir: Path, work: Path
) -> None:
    """A binary-safe copy, proven on bytes a text-mode copy would mangle.

    ``0x0D 0x0A`` is the pair that a file opened in text mode rewrites on
    Windows, and a save is full of them. This is the sibling case of the hash
    test: same root cause, different input.
    """
    source = pretend_account_dir / "AllBytes.sav"
    source.write_bytes(bytes(range(256)) * 8)

    copy = workdir.copy_for_read(source, work_root=work)

    assert copy.read_bytes() == source.read_bytes(), "the copy is not binary-safe"


# ===========================================================================
# 2. The source is provably untouched
# ===========================================================================


def test_the_source_is_untouched_by_the_copy(pretend_source: Path, work: Path) -> None:
    """Size, st_mtime_ns and sha256 are all identical across the copy.

    ``st_mtime_ns`` is the load-bearing one. A file opened for append and then
    closed without a write has the same size and the same hash; only the
    modification time moves. Nanoseconds rather than seconds because a
    whole-second field is too coarse to see a change made microseconds ago.
    """
    before = stat_triple(pretend_source)

    workdir.copy_for_read(pretend_source, work_root=work)

    after = stat_triple(pretend_source)
    assert after[0] == before[0], "the source size changed"
    assert after[1] == before[1], "the source modification time changed - it was opened for write"
    assert after[2] == before[2], "the source bytes changed"


def test_repeated_copies_leave_the_source_untouched(pretend_source: Path, work: Path) -> None:
    """The invariant holds under repetition, not only on the first call."""
    before = stat_triple(pretend_source)

    for _ in range(3):
        workdir.copy_for_read(pretend_source, work_root=work)

    assert stat_triple(pretend_source) == before, "a repeated copy disturbed the source"


# ===========================================================================
# 3. The destination refusal
# ===========================================================================


def test_a_destination_inside_the_save_root_is_refused(
    pretend_source: Path, pretend_save_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A work root inside the save root is refused - this is the never-write rule in code."""
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))

    with pytest.raises(workdir.DestinationRefusedError):
        workdir.copy_for_read(pretend_source, work_root=pretend_save_root / "work")


def test_a_destination_inside_the_account_directory_is_refused(
    pretend_source: Path,
    pretend_save_root: Path,
    pretend_account_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The account directory is refused too, not merely the save root above it."""
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))
    monkeypatch.setenv(ENV_ACCOUNT_DIR, str(pretend_account_dir))

    with pytest.raises(workdir.DestinationRefusedError):
        workdir.copy_for_read(pretend_source, work_root=pretend_account_dir / "work")


def test_a_destination_inside_the_game_install_is_refused(
    pretend_source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The install is read-only material and is refused as a destination."""
    install = tmp_path / "pretend_install"
    install.mkdir()
    monkeypatch.setenv(ENV_GAME_DIR, str(install))

    with pytest.raises(workdir.DestinationRefusedError):
        workdir.copy_for_read(pretend_source, work_root=install / "work")


def test_a_destination_reaching_the_save_root_by_traversal_is_refused(
    pretend_source: Path, pretend_save_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A '..' traversal must not defeat the check - both sides are resolved first.

    The path spelled here is lexically outside the save root and resolves to
    somewhere inside it. A check written against the string rather than against
    the resolved path passes this and writes into the save directory.
    """
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))
    traversal = pretend_save_root / "sibling" / ".." / PRETEND_ACCOUNT / "work"

    with pytest.raises(workdir.DestinationRefusedError):
        workdir.copy_for_read(pretend_source, work_root=traversal)


def test_a_destination_reaching_the_save_root_by_symlink_is_refused(
    pretend_source: Path,
    pretend_save_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A symlink pointing into the save root must not defeat the check either.

    SKIPS WITH A REASON where the platform will not create a symlink unelevated
    - Windows needs Developer Mode or an elevated process. A skip keeps the
    exit code at zero and stays visible in the ``-ra`` summary, which is the
    project's rule for a test that cannot run here rather than one that has
    been quietly deleted.
    """
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))
    link = tmp_path / "link_into_saves"
    try:
        link.symlink_to(pretend_save_root, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"this platform will not create a directory symlink here: {type(exc).__name__}")

    with pytest.raises(workdir.DestinationRefusedError):
        workdir.copy_for_read(pretend_source, work_root=link / "work")


def test_a_refused_destination_is_not_created(
    pretend_source: Path, pretend_save_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The refusal happens BEFORE any directory is made.

    Ordering is the whole point. A check that ran after mkdir would already
    have written into the save directory by the time it refused, and the
    exception would be a report of a violation rather than a prevention of one.
    """
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))
    forbidden = pretend_save_root / "work"

    with pytest.raises(workdir.DestinationRefusedError):
        workdir.copy_for_read(pretend_source, work_root=forbidden)

    assert not forbidden.exists(), "the refusal created the directory it was refusing"


def test_a_permitted_destination_outside_both_roots_is_allowed(
    pretend_source: Path, pretend_save_root: Path, work: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The refusal is narrow. A guard that refused everything would pass every test above."""
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))

    copy = workdir.copy_for_read(pretend_source, work_root=work)

    assert copy.is_file(), "a legitimate destination outside both roots was refused"


def test_the_refusal_message_carries_no_raw_account_directory(
    pretend_source: Path, pretend_save_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every path in an exception goes through locate.redact() first.

    Asserted on the rendered message rather than on the call, because the leak
    this prevents happens at the render site. The account directory name is a
    platform account id (CLAUDE.md non-negotiable 3) and a message quoting one
    into a log or an issue is the leak.
    """
    monkeypatch.setenv(ENV_SAVE_ROOT, str(pretend_save_root))

    with pytest.raises(workdir.DestinationRefusedError) as caught:
        workdir.copy_for_read(pretend_source, work_root=pretend_save_root / PRETEND_ACCOUNT)

    message = str(caught.value)
    assert PRETEND_ACCOUNT not in message, "the refusal message leaks the account directory"
    assert "\\" not in message, "the message was not passed through redact()"


# ===========================================================================
# The error surface
# ===========================================================================


def test_the_error_types_share_one_base() -> None:
    """A caller can catch WorkDirError and be sure it caught all of them."""
    assert issubclass(workdir.SourceUnreadableError, workdir.WorkDirError)
    assert issubclass(workdir.DestinationRefusedError, workdir.WorkDirError)


def test_a_missing_source_raises_source_unreadable(tmp_path: Path, work: Path) -> None:
    """An absent source is a stated error, not an OSError leaking from the copy."""
    with pytest.raises(workdir.SourceUnreadableError):
        workdir.copy_for_read(tmp_path / "no-such-file.sav", work_root=work)


def test_a_directory_given_as_a_source_raises_source_unreadable(tmp_path: Path, work: Path) -> None:
    """A directory is not a readable save, and says so rather than half-copying."""
    with pytest.raises(workdir.SourceUnreadableError):
        workdir.copy_for_read(tmp_path, work_root=work)


def test_a_missing_source_message_carries_no_raw_path(
    pretend_account_dir: Path, work: Path
) -> None:
    """The unreadable-source message is redacted too, not only the refusal message."""
    with pytest.raises(workdir.SourceUnreadableError) as caught:
        workdir.copy_for_read(pretend_account_dir / "Absent.sav", work_root=work)

    message = str(caught.value)
    assert PRETEND_ACCOUNT not in message, "the message leaks the account directory"
    assert "\\" not in message, "the message was not passed through redact()"


# ===========================================================================
# 4. latest_save across manual saves and autosaves
# ===========================================================================


def write_with_mtime(path: Path, payload: bytes, mtime_ns: int) -> Path:
    """Create a file with an exact modification time.

    Set explicitly rather than by sleeping between writes: an ordering test
    that depends on wall-clock granularity is the flaky test this avoids.
    """
    path.write_bytes(payload)
    os.utime(path, ns=(mtime_ns, mtime_ns))
    return path


def test_latest_save_picks_the_newest_across_manual_saves_and_autosaves(
    pretend_account_dir: Path, save_bytes: bytes
) -> None:
    """The newest wins whether it is a manual save or an autosave.

    Both live in the same directory and differ only by filename
    (BOOTSTRAP.md section 8.2 and the naming row in section 2), so the winner
    here is an autosave sitting between two manual saves in time.
    """
    base = 1_600_000_000_000_000_000
    write_with_mtime(pretend_account_dir / "World_010101-000000.sav", save_bytes, base)
    write_with_mtime(pretend_account_dir / "World_020202-000000.sav", save_bytes, base + 2_000)
    newest = write_with_mtime(
        pretend_account_dir / "World_autosave_1.sav", save_bytes, base + 9_000
    )
    write_with_mtime(pretend_account_dir / "World_autosave_0.sav", save_bytes, base + 1_000)

    assert workdir.latest_save(pretend_account_dir) == newest


def test_latest_save_picks_a_manual_save_when_it_is_the_newest(
    pretend_account_dir: Path, save_bytes: bytes
) -> None:
    """The mirror of the test above, so neither kind is preferred by construction."""
    base = 1_600_000_000_000_000_000
    write_with_mtime(pretend_account_dir / "World_autosave_0.sav", save_bytes, base)
    newest = write_with_mtime(
        pretend_account_dir / "World_030303-000000.sav", save_bytes, base + 5_000
    )

    assert workdir.latest_save(pretend_account_dir) == newest


def test_latest_save_ignores_files_that_are_not_saves(
    pretend_account_dir: Path, save_bytes: bytes
) -> None:
    """A newer non-save file does not win. Only .sav is a save."""
    base = 1_600_000_000_000_000_000
    newest_save = write_with_mtime(pretend_account_dir / "World.sav", save_bytes, base)
    write_with_mtime(pretend_account_dir / "notes.txt", b"not a save", base + 9_000)

    assert workdir.latest_save(pretend_account_dir) == newest_save


def test_latest_save_returns_none_for_an_empty_directory(pretend_account_dir: Path) -> None:
    """Absent content is reported, never fatal (CLAUDE.md non-negotiable 7)."""
    assert workdir.latest_save(pretend_account_dir) is None


def test_latest_save_returns_none_for_an_absent_directory(tmp_path: Path) -> None:
    """A directory that does not exist returns None rather than raising."""
    assert workdir.latest_save(tmp_path / "no-such-directory") is None


def test_latest_save_returns_none_when_nothing_resolves() -> None:
    """With no account directory resolvable, the answer is None, not an exception.

    This is the state of a machine that has never had the game installed, which
    the whole suite has to run green on. The autouse fixture is what forces
    that state here, on a machine where the game IS installed.
    """
    assert workdir.latest_save() is None


def test_latest_save_is_stable_across_two_runs(
    pretend_account_dir: Path, save_bytes: bytes
) -> None:
    """Two runs over the same directory agree, including on a modification-time tie.

    An advisor that disagrees with itself between runs is a bug (CLAUDE.md
    section 1), and a tie broken by directory order is exactly how that
    happens. The tie is constructed here rather than hoped for.
    """
    base = 1_600_000_000_000_000_000
    for name in ("Bravo.sav", "Alpha.sav", "Charlie.sav"):
        write_with_mtime(pretend_account_dir / name, save_bytes, base)

    first = workdir.latest_save(pretend_account_dir)
    second = workdir.latest_save(pretend_account_dir)
    assert first == second, "two runs over one directory disagreed"
    assert first is not None
    assert first.name == "Alpha.sav", "the tiebreak is not the documented one"


# ===========================================================================
# 5. purge_work_dir removes only what this module created
# ===========================================================================


def test_purge_removes_the_copies_this_module_made(pretend_source: Path, work: Path) -> None:
    """The copies go, and the count returned is the number actually removed."""
    workdir.copy_for_read(pretend_source, work_root=work)

    removed = workdir.purge_work_dir(work_root=work)

    assert removed == EXPECT_AT_LEAST_ONE, "purge did not report the copy it removed"
    assert workdir.purge_work_dir(work_root=work) == EXPECT_NONE, "purge is not idempotent"


def test_purge_removes_only_this_modules_copies(pretend_source: Path, work: Path) -> None:
    """An unrelated file planted in the work root SURVIVES.

    Two independent conditions have to hold for a file to be removed - it lives
    in the module's own copies directory AND it carries the module's suffix -
    so this plants a file that fails each condition separately. A purge keyed
    on the directory alone would delete the second one.
    """
    copy = workdir.copy_for_read(pretend_source, work_root=work)

    bystander = work / "operator-notes.txt"
    bystander.write_bytes(b"not ours")
    neighbour = copy.parent / "operator-notes.txt"
    neighbour.write_bytes(b"not ours either")

    removed = workdir.purge_work_dir(work_root=work)

    assert removed == EXPECT_AT_LEAST_ONE
    assert not copy.exists(), "purge left the copy behind"
    assert bystander.is_file(), "purge deleted an unrelated file in the work root"
    assert neighbour.is_file(), "purge deleted an unrelated file in the copies directory"


def test_purge_leaves_a_subdirectory_alone(pretend_source: Path, work: Path) -> None:
    """A directory is never removed, only files this module wrote."""
    workdir.copy_for_read(pretend_source, work_root=work)
    nested = work / "operator-scratch"
    nested.mkdir()

    workdir.purge_work_dir(work_root=work)

    assert nested.is_dir(), "purge removed a directory it did not create"


def test_purge_of_an_absent_work_root_is_zero_not_an_error(tmp_path: Path) -> None:
    """Nothing to purge is zero, not an exception and not a created directory."""
    absent = tmp_path / "never-created"

    assert workdir.purge_work_dir(work_root=absent) == EXPECT_NONE
    assert not absent.exists(), "purge created the work root it was asked to empty"


# ===========================================================================
# work_root itself
# ===========================================================================


def test_work_root_defaults_to_work_under_the_repo_root() -> None:
    """The default is <repo>/work, derived from the module's own location."""
    root = workdir.work_root()

    assert root.name == "work"
    assert root.parent == REPO_ROOT, "the default work root is not under the repo root"


def test_work_root_is_environment_overridable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The override is a CLOCKSPEED_-prefixed environment name, as the rest of the layer is."""
    assert workdir.ENV_WORK_ROOT.startswith("CLOCKSPEED_")
    monkeypatch.setenv(workdir.ENV_WORK_ROOT, str(tmp_path / "elsewhere"))

    assert workdir.work_root() == tmp_path / "elsewhere"


def test_work_root_does_not_create_anything() -> None:
    """Asking where the work root is must not make one.

    ``work_root()`` is a question. A resolver with a side effect would create a
    directory in the repo on any machine that merely imported the module and
    asked, including a machine with no game and no save.
    """
    root = workdir.work_root()
    existed = root.exists()

    workdir.work_root()

    assert root.exists() == existed, "work_root() created the directory it reports"


def test_the_default_work_root_is_gitignored() -> None:
    """/work/ must stay ignored: the copies are real saves and carry PII.

    Asked of git rather than asserted against the text of .gitignore, because
    what matters is the effective ignore decision and not the presence of a
    line. SKIPS WITH A REASON when git is unavailable.
    """
    probe = workdir.work_root() / "SyntheticWorld.sav"
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(probe)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=_CHILD_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        pytest.skip(f"git is not usable here: {type(exc).__name__}")

    ignored = result.returncode
    assert ignored == 0, (
        "the default work root is NOT gitignored. The copies under it are real saves and "
        "carry the platform account id and the player display name."
    )


# ===========================================================================
# 6. The no-write proof, in a child interpreter
# ===========================================================================

# Installs a RECORDING audit hook BEFORE importing the module under test, runs
# one copy, then classifies what the interpreter actually did.
#
# A recording spy rather than a raising one, deliberately: a hook that raised on
# the first write-intent event would abort the run at the first finding and
# report one violation where there may be several, and an exception raised
# inside an audit hook unwinds through whatever code triggered it, which makes
# the traceback a story about the hook rather than about the write.
#
# The child emits COUNTS AND EVENT NAMES ONLY, never a path. The pretend save
# root lives under the temporary directory, whose Windows 8.3 rendering spells
# the operator's account name as six characters plus a tilde and a digit
# (clockspeed/data/locate.py documents that exact leak), so printing the paths
# it classified would put an account name in the CI log.
_PROBE_NO_WRITE = """
import json
import os
import sys
from pathlib import Path

SAVE_ROOT, SOURCE, WORK = sys.argv[1], sys.argv[2], sys.argv[3]

WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
WRITE_MODE_CHARS = frozenset("wax+")

MUTATING = frozenset({
    "os.rename", "os.replace", "os.remove", "os.unlink", "os.mkdir", "os.rmdir",
    "os.truncate", "os.chmod", "os.chown", "os.utime", "os.link", "os.symlink",
    "os.setxattr", "os.removexattr", "shutil.copyfile", "shutil.copymode",
    "shutil.copystat", "shutil.move", "shutil.rmtree", "shutil.unpack_archive",
})

RECORDS = []
RECORDING = [True]


def texts(args):
    out = []
    for item in args:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, bytes):
            out.append(item.decode("utf-8", "replace"))
        elif isinstance(item, os.PathLike):
            out.append(os.fspath(item))
    return out


def hook(event, args):
    if not RECORDING[0]:
        return
    if event == "open":
        mode = args[1] if len(args) > 1 and isinstance(args[1], str) else ""
        flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
        RECORDS.append(("open", texts(args[:1]), mode, flags))
    elif event in MUTATING:
        RECORDS.append((event, texts(args), "", 0))


sys.addaudithook(hook)

from clockspeed.save import workdir

copy = workdir.copy_for_read(Path(SOURCE), work_root=Path(WORK))

# Stop recording BEFORE classifying: resolve() below raises its own events, and
# a list being appended to while it is iterated is a different bug entirely.
RECORDING[0] = False

root = Path(SAVE_ROOT).resolve()


def under_save_root(text):
    try:
        return Path(text).resolve().is_relative_to(root)
    except (OSError, ValueError):
        return False


write_intent = 0
mutating = 0
read_opens = 0
offenders = []

for event, paths, mode, flags in RECORDS:
    if not any(under_save_root(p) for p in paths):
        continue
    if event == "open":
        if (WRITE_MODE_CHARS & set(mode)) or (flags & WRITE_FLAGS):
            write_intent += 1
            offenders.append("open(mode=" + mode + ")")
        else:
            read_opens += 1
    else:
        mutating += 1
        offenders.append(event)

print(json.dumps({
    "write_intent_under_save_root": write_intent,
    "mutating_under_save_root": mutating,
    "read_opens_under_save_root": read_opens,
    "offending_event_names": sorted(set(offenders)),
    "events_seen": len(RECORDS),
    "copy_exists": copy.is_file(),
    "copy_under_work": copy.resolve().is_relative_to(Path(WORK).resolve()),
}))
"""


def run_child(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run a child interpreter from the repo root and capture its output.

    ``sys.executable`` is the only correct way to name the interpreter: a bare
    name would resolve off PATH to whatever happens to be first, and an
    absolute interpreter path in a tracked file is forbidden outright.

    Callers bind ``returncode`` to a local before asserting on it. That is not
    style - asserting on the CompletedProcess makes pytest repr ``args[0]``,
    the absolute interpreter path, which on a default install sits under the
    operator's home directory and carries their account name into the log. The
    same discipline is recorded at tests/data/test_phase2_gate.py::run_child.
    """
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_CHILD_TIMEOUT_SECONDS,
        env=env,
        check=False,
    )


def isolated_env(**overrides: str) -> dict[str, str]:
    """A child environment with every resolver pointed at nothing, then overridden."""
    env = dict(os.environ)
    env[ENV_GAME_DIR] = str(ABSENT / "install")
    env[ENV_SAVE_ROOT] = str(ABSENT / "saves")
    env[ENV_ACCOUNT_DIR] = str(ABSENT / "account")
    env[ENV_LOCAL_CONFIG] = str(ABSENT / "local.json")
    env.pop(workdir.ENV_WORK_ROOT, None)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env.update(overrides)
    return env


def test_no_write_intent_event_reaches_the_save_root(
    pretend_source: Path, pretend_save_root: Path, work: Path
) -> None:
    """The interpreter's own audit stream says the save root was only ever read.

    Three assertions, and the third is the one that gives the other two their
    meaning. "No writes happened" is trivially true of a function that never
    ran, so the count of READ opens under the pretend save root is asserted
    non-zero in the same test. Without it this passes against a ``copy_for_read``
    whose body is ``pass``.
    """
    env = isolated_env(**{ENV_SAVE_ROOT: str(pretend_save_root)})
    child = run_child(
        ["-c", _PROBE_NO_WRITE, str(pretend_save_root), str(pretend_source), str(work)], env
    )

    exit_code = child.returncode
    assert exit_code == 0, (
        f"the audit probe failed:\nstdout:\n{child.stdout}\nstderr:\n{child.stderr}"
    )

    report = json.loads(child.stdout)
    write_intent = report["write_intent_under_save_root"]
    mutating = report["mutating_under_save_root"]
    read_opens = report["read_opens_under_save_root"]
    offenders = report["offending_event_names"]

    assert write_intent == EXPECT_NONE, (
        f"{write_intent} write-intent open(s) targeted the save root: {offenders}"
    )
    assert mutating == EXPECT_NONE, (
        f"{mutating} mutating event(s) targeted the save root: {offenders}"
    )
    assert read_opens >= EXPECT_AT_LEAST_ONE, (
        "no read open under the save root was recorded, so this test proves nothing - "
        "copy_for_read did not read the source at all"
    )
    assert report["copy_exists"] is True
    assert report["copy_under_work"] is True


def test_the_audit_probe_can_actually_see_a_write(
    pretend_source: Path, pretend_save_root: Path, work: Path
) -> None:
    """The detector is proven to detect, on a deliberate write into the save root.

    A guard is a claim until it has been shown failing. This runs the same
    classification over a child that DOES write into the pretend save root and
    asserts the count comes back non-zero - so a hook that silently stopped
    recording, or a mask that matched nothing, turns this red instead of
    leaving the test above passing for the wrong reason.
    """
    culprit = _PROBE_NO_WRITE.replace(
        "copy = workdir.copy_for_read(Path(SOURCE), work_root=Path(WORK))",
        "copy = workdir.copy_for_read(Path(SOURCE), work_root=Path(WORK))\n"
        "(Path(SAVE_ROOT) / 'deliberate.tmp').write_bytes(b'x')",
    )
    assert culprit != _PROBE_NO_WRITE, "the probe source changed and this self-test is stale"

    env = isolated_env(**{ENV_SAVE_ROOT: str(pretend_save_root)})
    child = run_child(
        ["-c", culprit, str(pretend_save_root), str(pretend_source), str(work / "b")], env
    )

    exit_code = child.returncode
    assert exit_code == 0, f"the self-test probe failed:\n{child.stdout}\n{child.stderr}"

    report = json.loads(child.stdout)
    write_intent = report["write_intent_under_save_root"]
    assert write_intent >= EXPECT_AT_LEAST_ONE, (
        "the audit probe did not notice a deliberate write into the save root, "
        "so it cannot be trusted to notice an accidental one"
    )


# ===========================================================================
# 7. The whole suite, with no install and no save
# ===========================================================================

_RECURSING_TEST = "test_the_workdir_suite_passes_with_no_install_and_no_save"

# A pytest NODE ID, which is not a path: it is relative to the rootdir and uses
# forward slashes on every platform. Measured, after the absolute-Windows-path
# form silently matched nothing - `--deselect` accepts an id it cannot find
# without a word of complaint, the child then ran the recursing test, and that
# spawned a subprocess chain that only stopped at the timeout.
# ``test_the_child_run_deselects_only_the_recursing_test`` is what caught it,
# which is the whole reason that test exists.
_MODULE_NODE_ID = THIS_MODULE.relative_to(REPO_ROOT).as_posix()


def _child_pytest_args() -> list[str]:
    """Run this module in a child, minus the one test that would recurse."""
    return [
        "-m",
        "pytest",
        _MODULE_NODE_ID,
        f"--deselect={_MODULE_NODE_ID}::{_RECURSING_TEST}",
        "-p",
        "no:cacheprovider",
        "-q",
    ]


def test_the_workdir_suite_passes_with_no_install_and_no_save() -> None:
    """This module exits zero with all four overrides pointed at a nonexistent path.

    The rule suite has to run on a machine that has never had the game on it.
    A test here that reached for the real save root, the real install or the
    operator's config/local.json turns this red on the machine where the game
    IS installed - the only machine where the mistake is otherwise invisible.
    """
    child = run_child(_child_pytest_args(), isolated_env())

    exit_code = child.returncode
    assert exit_code == 0, (
        "the workdir suite does not pass without an install or a save.\n"
        f"exit code: {exit_code}\nstdout:\n{child.stdout}\nstderr:\n{child.stderr}"
    )
    passed = re.search(r"(\d+) passed", child.stdout)
    assert passed is not None, f"the child run reported no passing tests:\n{child.stdout}"
    assert int(passed.group(1)) >= EXPECT_AT_LEAST_ONE


def test_the_child_run_deselects_only_the_recursing_test() -> None:
    """The recursion guard is verified against pytest's own collection, not assumed.

    ``--deselect`` silently accepts a node id it does not match, so "the guard
    works" is a claim until pytest is asked what it collected. Both halves
    matter: the recursing test absent, and the rest of this module present. A
    guard that deselected everything would also make the test above pass.
    """
    # NOT a second -q. Two of them collapse --collect-only to a bare count,
    # and a count contains no test name, so every assertion below would be
    # asserting against an empty haystack.
    child = run_child([*_child_pytest_args(), "--collect-only"], isolated_env())

    exit_code = child.returncode
    assert exit_code == 0, f"collection failed:\n{child.stdout}\n{child.stderr}"

    collected = child.stdout
    assert _RECURSING_TEST not in collected, "the child collects the recursing test"
    for sibling in (
        "test_the_copy_is_byte_identical_to_the_source",
        "test_the_source_is_untouched_by_the_copy",
        "test_purge_removes_only_this_modules_copies",
    ):
        assert sibling in collected, (
            f"the child run collects no {sibling}; the deselect is too wide and the gate "
            "would pass by testing nothing"
        )


# ===========================================================================
# The single-writer commitment (docs/adr/0007 Decision item 6)
# ===========================================================================


def test_workdir_is_the_only_save_module_that_can_write() -> None:
    """No sibling in clockspeed/save/ opens a file for write.

    docs/adr/0007 Decision item 6 states this as a COMMITMENT that a later gate
    converts into a static assertion. This is the narrow, local form of it: a
    text scan of the sibling modules for a write-capable open. It is not the
    AST gate that item promises and does not claim to be - it is the check that
    keeps the property true between now and then.
    """
    package = REPO_ROOT / "clockspeed" / "save"

    offenders = {
        module.name: modes
        for module in sorted(package.glob("*.py"))
        if module.name != "workdir.py"
        and (modes := write_modes_in(module.read_text(encoding="utf-8")))
    }

    assert offenders == {}, (
        "these save modules open a file for write, but workdir.py owns the only write "
        f"in the package: {offenders}"
    )


def test_the_single_writer_detector_actually_detects() -> None:
    """The detector above is shown finding a write, so a green result means something.

    The last two cases are the false positive the naive form of this check has:
    a read open whose FILENAME happens to contain a mode character.
    """
    assert write_modes_in('with path.open("wb") as fh:') == ["wb"]
    assert write_modes_in("with path.open('a') as fh:") == ["a"]
    assert write_modes_in('with open(target, "w+") as fh:') == ["w+"]
    assert write_modes_in('with path.open("rb") as fh:') == []
    assert write_modes_in('with open("data.txt") as fh:') == []
    assert write_modes_in('with open(path, "rb") as fh:') == []
