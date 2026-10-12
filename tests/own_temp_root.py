"""CS-1319 - give this suite its own temp root, so a killed run cannot bloat the shared one.

THE DEFECT, measured by MAIN on 2026-10-12. pytest puts every run under one
per-account root in the system temp directory, ``pytest-of-<user>``, shared by
every tree on the machine. A run that is killed or fails leaves its numbered
directory behind with its lock file, and pytest's keep-N retention will not
reclaim a locked directory for three days. One night of this suite's runs left
about seventy thousand directories there, and the temp directory count costs
boot time on this machine.

THE MECHANISM. :func:`install`, called from the root conftest's
``pytest_configure``, claims a fresh directory ``run-<pid>-<token>`` under the
tree-owned root ``<temp>/clockspeed-pytest`` and points
``PYTEST_DEBUG_TEMPROOT`` at it, so pytest builds its usual
``pytest-of-<user>/pytest-<N>`` layout INSIDE that run directory. The variable
is inherited, so xdist workers and nested pytest runs land there too, and a
nested run that clears it claims a run directory of its own.

  - A claim never overrides a root already named in the environment, and an
    explicit ``--basetemp`` claims nothing: whoever chose the place owns it.
  - A clean finish removes the whole run directory. A FAILED top-level run
    (exit 1, 2 or 3) keeps it, marked :data:`FAILED_NAME` so the next sweep
    keeps it until :data:`STALE_AFTER_S` on every platform, the newest
    :data:`KEEP_FAILED` only:
    ``tmp_path_retention_policy = "failed"`` keeps exactly the failing tests'
    directories, and they are the only record of what a flake wrote. Exit 0,
    4 (usage error) and 5 (nothing collected) remove it. A NESTED run - a
    pytest a test spawned, marked by :data:`ENV_NESTED` - removes its directory
    whatever its exit status: the first whole suite under this mechanism left
    36 of them, failing on purpose.
  - A killed run never reaches its finish, so every claim first sweeps its
    siblings. On Windows each owner holds :data:`ALIVE_NAME` open for its
    life, so a run whose marker can be unlinked has no live owner and is
    reclaimed at once, and a held marker keeps a run however old it is;
    elsewhere a run older than :data:`STALE_AFTER_S` is reclaimed. Nothing
    inside :data:`GRACE_S` is touched, and no link or junction ever is.
  - A claim that cannot make its directory owns nothing and raises nothing:
    pytest falls back to its default rather than stopping the session.
  - Removal clears the read-only attribute and retries, ON THE ENTRY ITSELF and
    never through a link, and never follows a junction or a symlink out of the
    tree - ``tests/save/test_workdir.py`` plants read-only links and junctions
    pointing at directories that must survive.

Nothing here raises out of a hook: a removal that still fails is left for the
next sweep, never a red session.
"""

from __future__ import annotations

import contextlib
import os
import secrets
import shutil
import stat
import tempfile
import time
from collections.abc import Callable, MutableMapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Final

import pytest

#: The variable pytest reads for the directory it builds ``pytest-of-<user>`` in.
ENV_TEMPROOT: Final = "PYTEST_DEBUG_TEMPROOT"

#: The tree-owned root's name, directly under the system temp directory.
ROOT_NAME: Final = "clockspeed-pytest"

#: Every run directory's name starts with this; the sweep touches nothing else.
RUN_PREFIX: Final = "run-"

#: A run directory older than this is a killed run's wherever its owner's
#: liveness cannot be read. A whole suite takes minutes, so six hours never
#: reaches a live one.
STALE_AFTER_S: Final = 6 * 3600.0

#: A run directory younger than this is never swept: a sibling may be between
#: its mkdir and the open of its marker.
GRACE_S: Final = 120.0

#: The marker each owner holds open for its whole life, inside its run directory.
ALIVE_NAME: Final = ".alive"

#: Written by a failed top-level run at its finish: its retained tmp_paths are
#: kept until :data:`STALE_AFTER_S`, on every platform, though its owner is gone.
FAILED_NAME: Final = ".failed"

#: How many failed runs' directories the sweep keeps, newest first. One failed
#: whole suite kept about sixteen thousand directories when measured, so a
#: night of failures must not stack them; the newest is the one investigated.
KEEP_FAILED: Final = 1

#: The exit statuses whose run keeps its directory: tests failed, interrupted,
#: internal error. A clean run, a usage error and an empty collection have no
#: record worth keeping.
KEEP_STATUSES: Final = frozenset({1, 2, 3})

#: Set by a top-level claim, inherited by everything it spawns: a claim that
#: finds it is a NESTED run - a pytest a test started - and keeps nothing.
ENV_NESTED: Final = "CLOCKSPEED_PYTEST_NESTED"

#: The plugin name the finisher registers under, so it is registered once.
PLUGIN_NAME: Final = "cs1319-own-temp-root"


def own_root() -> Path:
    """The tree-owned temp root, under the system temp directory."""
    return Path(tempfile.gettempdir()) / ROOT_NAME


def _is_link(path: Path) -> bool:
    """A symlink or a junction - an entry whose target is never touched."""
    return path.is_symlink() or path.is_junction()


def _clear_read_only_and_retry(func: Callable[..., object], path: str, _exc: BaseException) -> None:
    """``shutil.rmtree``'s ``onexc``: make the entry itself writable, then retry once.

    The attribute is cleared on the entry and never through it: on a link or a
    junction only where ``os.chmod`` can act on the link itself. A retry that
    fails again is swallowed - the next sweep gets another try.
    """
    entry = Path(path)
    with contextlib.suppress(OSError):
        if os.chmod in os.supports_follow_symlinks:
            entry.chmod(stat.S_IWRITE | stat.S_IREAD, follow_symlinks=False)
        elif not _is_link(entry):
            entry.chmod(stat.S_IWRITE | stat.S_IREAD)
        func(path)


def remove_tree(path: Path) -> None:
    """Remove ``path`` and everything under it, read-only entries included.

    ``shutil.rmtree`` removes a symlink or a junction INSIDE the tree as an
    entry and never walks into it. A ``path`` that is itself a link is
    unlinked, not followed. A missing ``path`` is not an error.
    """
    if _is_link(path):
        try:
            path.unlink()
        except OSError as exc:
            _clear_read_only_and_retry(os.unlink, str(path), exc)
        return
    if path.is_dir():
        shutil.rmtree(_extended(path), onexc=_clear_read_only_and_retry)


def _extended(path: Path) -> str:
    """``path`` in the Windows extended-length form; unchanged elsewhere.

    The Win32 path layer strips a trailing dot or space from every component,
    so a file named ``zz.`` - which the inbox arms plant - cannot be unlinked
    by a plain path, and the directory above it then cannot be removed.
    The extended-length prefix passes every name through unnormalised.
    """
    if os.name != "nt":
        return str(path)
    full = str(path.absolute())
    if full.startswith("\\\\?\\"):
        return full
    if full.startswith("\\\\"):
        return "\\\\?\\UNC\\" + full[2:]
    return "\\\\?\\" + full


@dataclass
class Claim:
    """One claimed run directory and the handle that marks its owner alive."""

    path: Path
    nested: bool
    alive: BinaryIO | None = field(default=None, repr=False)


def _owner_is_gone(run: Path) -> bool:
    """Whether ``run``'s owner has provably exited - Windows only.

    A live owner holds its :data:`ALIVE_NAME` marker open and Windows refuses
    to unlink an open file, so a successful unlink proves no live owner. A
    missing marker past the grace period is an owner that never opened one or
    already finished. Elsewhere an unlink always succeeds, so nothing is
    provable. Called only on a real directory, never on a link, so the unlink
    can never reach through one.
    """
    if os.name != "nt":
        return False
    try:
        (run / ALIVE_NAME).unlink()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return True


def _classify(entry: os.DirEntry[str], clock: float) -> tuple[float | None, Path] | None:
    """One sweep verdict: None to keep, ``(None, run)`` to remove, or ``(age, run)``.

    The last is a failed run inside the stale age: kept or removed by
    :func:`sweep` once every failed run's age is known.
    """
    if not entry.name.startswith(RUN_PREFIX):
        return None
    run = Path(entry.path)
    try:
        if entry.is_symlink() or entry.is_junction() or not entry.is_dir(follow_symlinks=False):
            return None
        age = clock - entry.stat(follow_symlinks=False).st_mtime
    except OSError:
        return None
    if (run / FAILED_NAME).is_file():
        return (None, run) if age > STALE_AFTER_S else (age, run)
    if age <= GRACE_S:
        return None
    gone = _owner_is_gone(run) if os.name == "nt" else age > STALE_AFTER_S
    return (None, run) if gone else None


def sweep(parent: Path, now: float | None = None) -> int:
    """Remove every run directory under ``parent`` whose owner is gone.

    Gone means past :data:`GRACE_S` and, on Windows, provably exited
    (:func:`_owner_is_gone`) - whatever its age, so a live run open for hours
    keeps its tmp_paths; elsewhere, older than :data:`STALE_AFTER_S`. A run a
    failed finish marked with :data:`FAILED_NAME` is kept until
    :data:`STALE_AFTER_S` everywhere, and only the newest :data:`KEEP_FAILED`
    of them. An entry that is a link or a junction is
    never touched: no claim makes one.

    Args:
        parent: The tree-owned root.
        now: The clock to age against; the wall clock when omitted.

    Returns:
        How many run directories were removed.
    """
    clock = time.time() if now is None else now
    try:
        entries = list(os.scandir(parent))
    except OSError:
        return 0
    doomed: list[Path] = []
    failed: list[tuple[float, Path]] = []
    for entry in entries:
        verdict = _classify(entry, clock)
        if verdict is None:
            continue
        failed_age, run = verdict
        if failed_age is None:
            doomed.append(run)
        else:
            failed.append((failed_age, run))
    failed.sort(key=lambda pair: pair[0])
    doomed.extend(run for _age, run in failed[KEEP_FAILED:])
    removed = 0
    for run in doomed:
        remove_tree(run)
        if not os.path.lexists(run):
            removed += 1
    return removed


def claim(parent: Path, env: MutableMapping[str, str]) -> Claim | None:
    """Claim a fresh run directory under ``parent`` and name it in ``env``.

    Args:
        parent: The tree-owned root; created when missing.
        env: The environment to set :data:`ENV_TEMPROOT` and :data:`ENV_NESTED` in.

    Returns:
        The claim, or None when ``env`` already names a temp root, or when the
        root or the run directory cannot be made - the caller then owns
        nothing, removes nothing, and pytest falls back to its default. This
        runs inside ``pytest_configure``, where a raise stops the session.
    """
    if env.get(ENV_TEMPROOT):
        return None
    nested = bool(env.get(ENV_NESTED))
    run: Path | None = None
    try:
        parent.mkdir(parents=True, exist_ok=True)
        sweep(parent)
        while True:
            run = parent / (RUN_PREFIX + str(os.getpid()) + "-" + secrets.token_hex(4))
            try:
                run.mkdir(mode=0o700)
            except FileExistsError:
                continue
            break
        alive = (run / ALIVE_NAME).open("wb")
    except OSError:
        if run is not None:
            remove_tree(run)
        return None
    env[ENV_TEMPROOT] = str(run)
    env[ENV_NESTED] = "1"
    return Claim(path=run, nested=nested, alive=alive)


def finish(run: Claim, exitstatus: int) -> None:
    """Remove a run's directory unless it is a failed top-level run's.

    A kept directory is marked with :data:`FAILED_NAME`, so the next claim's
    sweep keeps it until :data:`STALE_AFTER_S` rather than reclaiming it the
    moment its owner is gone.

    Args:
        run: The claim :func:`claim` returned.
        exitstatus: The session's exit status; zero is a clean run.
    """
    if run.alive is not None:
        with contextlib.suppress(OSError):
            run.alive.close()
        run.alive = None
    if run.nested or int(exitstatus) not in KEEP_STATUSES:
        remove_tree(run.path)
        return
    with contextlib.suppress(OSError):
        (run.path / FAILED_NAME).write_bytes(b"")


class _Finisher:
    """The session-finish hook for one claimed run directory."""

    def __init__(self, run: Claim) -> None:
        self.run = run

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, exitstatus: int) -> None:
        """After pytest's own temp retention has run, finish the run directory."""
        finish(self.run, exitstatus)


def install(config: pytest.Config) -> Claim | None:
    """Claim this session's run directory and register its finisher.

    An explicit ``--basetemp`` claims nothing, and neither does a process whose
    environment already names a temp root: an xdist worker, a nested run, or
    an operator's own choice.

    Args:
        config: The session's configuration.

    Returns:
        The claim, or None when this process owns none.
    """
    if config.getoption("basetemp", None) or config.pluginmanager.has_plugin(PLUGIN_NAME):
        return None
    run = claim(own_root(), os.environ)
    if run is not None:
        config.pluginmanager.register(_Finisher(run), PLUGIN_NAME)
    return run


def wrap_configure(namespace: dict[str, Any]) -> None:
    """Wrap the conftest's ``pytest_configure`` so :func:`install` runs first.

    Wrapped in place rather than edited: the conftest's line numbers are pinned
    by the deep archive, so its new blocks are appended at the foot. The
    wrapper keeps the original's ``trylast`` marker, and xdist hands its
    workers their base temp at session start, after every configure hook.

    Args:
        namespace: The conftest's ``globals()``.
    """
    original: Callable[[pytest.Config], None] = namespace["pytest_configure"]

    @pytest.hookimpl(trylast=True)
    def pytest_configure(config: pytest.Config) -> None:
        install(config)
        original(config)

    pytest_configure.__doc__ = original.__doc__
    namespace["pytest_configure"] = pytest_configure
