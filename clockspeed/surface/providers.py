"""The one module in this layer that reaches down for an input or touches a disk.

Owns (BOOTSTRAP.md section 7.1): the concrete :class:`~clockspeed.surface.api.
contract.WorldProvider` and :class:`~clockspeed.surface.api.contract.
RegistryProvider` the server binds into its handlers, the concrete
``advice.AdviceSource`` that reads the advisor's two stores (CS-1270), plus the
reader for the dashboard's own static assets.

WHY THIS MODULE EXISTS AT ALL. ``clockspeed/surface/api/__init__.py`` forbids an
endpoint from opening a file - "an endpoint that reaches for the filesystem has
reached past two neighbours at once" - and ``contract.py`` keeps both provider
protocols GENERIC so that the endpoint package names no layer below its
neighbour. Something still has to actually find a save and actually read the
shipped docs. That is this module, and concentrating it here is what makes "no
endpoint opens a file" a static fact about the tree rather than a rule reviewers
have to remember. ``tests/surface/test_server.py`` pins the allow-list.

NONE OF THESE PROVIDERS RAISES, AND THAT IS THE WHOLE POINT. "There is no game
installed on this machine" and "there is no save yet" are true answers about a
working system, not failures, so they are spelled ``None`` and become a 503
through ``contract.unavailable`` rather than a traceback through a 500 that this
surface does not even have a code for. Every reach downward below is wrapped, and
the wrap catches the documented refusal of the layer beneath plus ``OSError``,
because a file that vanished between the listing and the read is the ordinary
case on a machine where the game is running.

THIS MODULE READS AND NEVER WRITES. Non-negotiable 1: never write to the game
install or the save directory. The one copy any save load performs is
``clockspeed/save/workdir.copy_for_read``, which owns it, checks its destination
against the save root and the install BEFORE creating anything, and is the only
write in the save package. Nothing here bypasses it, and nothing here writes at
all - a sweep in ``tests/surface/test_server.py`` asserts that across the whole
package with no exceptions.

ONE PARSE PER SAVE IDENTITY (CS-1203). This module said "no caching,
deliberately" and re-read the world on every call, on the argument that a stale
world rendered as current is worse than a slow one. MEASURED FALSE AS A TRADE:
the parse outgrew the companion's per-probe timeout, ``/api/health`` asks for
the world on every request, and every probe aborted - slow became absent. The
invalidation rule that argument said would have to be invented is the file's
own identity: the resolved newest path, its size in bytes and its
``st_mtime_ns``, all three read fresh on EVERY call. THE GUARANTEE IS EXACTLY
THAT AND NO MORE: a rewrite that changes any of the three is re-read on the
next call, and a rewrite that preserves all three - same path, same size, the
modification time restored - is NOT detected and serves the previously parsed
world. An ordinary write moves the modification time on NTFS, so reaching that
case takes a deliberate restore. A re-read that fails answers None, never the
previous world. The remembered world is held by :class:`SaveWorldProvider`,
which is NOT a dataclass and inherits ``object.__repr__``, so
``tests/repr_rendering_guard.py`` rule R2 has no generated repr to grade; the
runtime arm that renders a provider AFTER a world is remembered is in
``tests/test_repr_rendering.py``.
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Final

from clockspeed.advisor.advise import advise_world
from clockspeed.advisor.ledger import CardState, Ledger, MuteStore, StoreError
from clockspeed.data import locate, registry, version
from clockspeed.data.docs_extract import DocsExtractError, load_document, read_docs_text
from clockspeed.save import workdir
from clockspeed.save.world import (
    SAVE_VERDICT_STAGES,
    WorldLoadError,
    load_newest_world,
    load_world,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence
    from pathlib import Path

    from clockspeed.advisor.advise import Advice
    from clockspeed.data.registry import Registry
    from clockspeed.save.world import WorldModel

__all__ = [
    "FORBIDDEN_IN_AN_ASSET_NAME",
    "InstalledRegistryProvider",
    "SaveWorldProvider",
    "StaticAssets",
    "StoreAdviceSource",
]

#: Substrings that must never appear in an asset name. The name always arrives
#: from a frozen table rather than from a request, so this can only fire if that
#: stops being true - which is exactly when it needs to.
FORBIDDEN_IN_AN_ASSET_NAME: Final = ("/", "\\", "..", ":")


class SaveWorldProvider:
    """Hands up the newest save on this machine, or says there is not one.

    Satisfies ``contract.WorldProvider[WorldModel]`` structurally; the protocol
    is ``runtime_checkable`` and a test asserts the isinstance rather than this
    class naming it as a base, so the seam stays one-directional.

    NOT A DATACLASS AND HOLDS NO ANNOTATED ``Path`` FIELD, so it is outside the
    population ``tests/repr_rendering_guard.py`` grades and inherits
    ``object.__repr__``, which renders no attribute at all. A dataclass here
    would render an account directory in full. The same holds for what it
    remembers: the identity tuple carries the resolved save path, and it lives
    only in private attributes that ``object.__repr__`` never reads.

    ONE PARSE PER IDENTITY, SHARED BY CONCURRENT CALLERS (CS-1203). The server
    is threaded, so a lock spans the resolve, the identity read and the load:
    a caller arriving while a parse is in flight waits for it, then reads the
    identity afresh. When that parse succeeded and the identity is unchanged,
    the caller is handed the remembered world rather than starting a second
    parse of the same bytes; when it was refused, what the caller does next is
    the next paragraph's.

    A SAVE THE READER REFUSES IS SKIPPED, NOT FATAL. The newest file is not
    always one the game wrote - a save re-encoded by a third-party tool is
    refused by the object reader - so the provider walks the whole
    newest-first ranking through ``world.load_newest_world``, which flags the
    newer saves it skipped on the world it hands up.

    ONLY A VERDICT ON THE SAVE'S OWN BYTES IS REMEMBERED. A refusal at a stage
    in ``world.SAVE_VERDICT_STAGES`` is kept by the same identity a world is,
    because the same bytes draw the same verdict: an unchanged refused save is
    not copied and parsed again on every probe, and a rewritten one is tried
    afresh. A failure at any other stage - the copy, which is the environment,
    and the property map, which is the install - is NEVER remembered and never
    falls back, so the next call tries the newest save again exactly as it did
    before this provider remembered anything. Only the refusals the current
    walk met are kept, so the memory is bounded by the ranking.

    WHAT IS KEPT IS THE REFUSAL ITSELF, WITH EVERY TRACEBACK DROPPED. The
    walk re-raises a remembered refusal rather than building a new one, so no
    ``WorldLoadError`` is ever constructed here from remembered strings - the
    message channel ``tests/test_exception_messages.py`` grades stays proven at
    the save layer's own sites. Its tracebacks, and its causes', are cleared
    after every walk: a traceback holds the reader's frames, and a frame can
    hold the decompressed body, which a memo must not keep alive.
    """

    def __init__(
        self,
        account_dir: Path | None = None,
        *,
        find_save: Callable[[Path | None], Path | None] | None = None,
        find_saves: Callable[[Path | None], Sequence[Path]] | None = None,
        load: Callable[[Path], WorldModel] = load_world,
    ) -> None:
        """Wire the provider, defaulting to the real save resolution.

        The seams are injectable so the suite can exercise every branch on a
        machine with NO GAME INSTALLED, which BOOTSTRAP.md section 8.1 requires
        of the whole rule suite. The defaults are what production runs.

        Args:
            account_dir: The directory to search, or None to resolve it from the
                environment, ``config/local.json`` and auto-detection. The value
                is a platform account directory and is never rendered.
            find_save: Picks ONE save, or None when there is not one - a ranking
                of at most one, so nothing is fallen back to. Kept for callers
                that pin the save; mutually exclusive with ``find_saves``.
            find_saves: Ranks the saves to try, newest first. Defaults to
                ``workdir.ranked_saves`` when neither seam is given.
            load: Copies a save out of harm's way and parses it.

        Raises:
            ValueError: Both ``find_save`` and ``find_saves`` were given.
        """
        if find_save is not None and find_saves is not None:
            raise ValueError("pass find_save or find_saves, not both")
        if find_saves is None:
            find_saves = workdir.ranked_saves if find_save is None else _at_most_one(find_save)
        self._account_dir = account_dir
        self._find_saves = find_saves
        self._load = load
        self._lock = threading.Lock()
        self._remembered: tuple[tuple[Path, int, int], WorldModel] | None = None
        self._refused: dict[tuple[Path, int, int], WorldLoadError] = {}

    def world(self) -> WorldModel | None:
        """The current world, or None when this machine has no save to read.

        Returns:
            The world model, or None. None covers all three of "no save
            directory", "an empty save directory" and "no save that would
            parse" - the endpoint tells the first two from the third through the
            reason it picks, not through an exception it has to catch. A world
            read from an older save past a refused newer one carries a
            ``WARN_NEWER_SAVE_REFUSED`` flag for what was skipped.

        A save whose identity - path, size, modification time - matches the
        last successful load is handed up without being copied or parsed
        again, and one matching a remembered verdict on its bytes is skipped
        without being copied or parsed again. Any other failed load is never
        remembered, so the next call retries it; a save whose identity cannot
        be read is loaded per call, exactly as before this provider remembered
        anything.
        """
        with self._lock:
            try:
                candidates = tuple(self._find_saves(self._account_dir))
            except OSError:
                return None
            if not candidates:
                self._remembered = None
                self._refused = {}
                return None
            refused: dict[tuple[Path, int, int], WorldLoadError] = {}
            try:
                return load_newest_world(
                    candidates, load=lambda path: self._remembering_load(path, refused)
                )
            except (WorldLoadError, OSError, ValueError):
                # Nothing in the ranking loaded, so nothing remembered is
                # current - release it rather than hold a world no call serves.
                self._remembered = None
                return None
            finally:
                for verdict in refused.values():
                    _drop_tracebacks(verdict)
                self._refused = refused

    def _remembering_load(
        self, path: Path, refused: dict[tuple[Path, int, int], WorldLoadError]
    ) -> WorldModel:
        """Load one candidate, answering from memory when its identity allows.

        Called with the lock held, once per candidate the walk tries.

        Args:
            path: The candidate.
            refused: This call's verdicts on save bytes by identity, filled in
                here and kept for the next call - only the current walk's.

        Returns:
            The remembered or freshly loaded world.

        Raises:
            WorldLoadError: The reader refused the save, now or - for an
                unchanged identity - on an earlier call, re-raised as the very
                refusal it was; or the load failed for a reason that is no
                verdict on the bytes, which is never remembered.
        """
        identity = _identity(path)
        if identity is not None:
            verdict = self._refused.get(identity)
            if verdict is not None:
                refused[identity] = verdict
                raise verdict
            remembered = self._remembered
            if remembered is not None and remembered[0] == identity:
                return remembered[1]
        # The remembered world is NOT dropped before this load: when the
        # candidate is a newer save the reader refuses, the remembered world
        # is the fallback the walk reaches next, and dropping it here cost a
        # second parse of a world already in memory. Serving it stays keyed on
        # an exact identity match, so a stale world is never handed up.
        try:
            world = self._load(path)
        except WorldLoadError as refusal:
            if identity is not None and refusal.stage in SAVE_VERDICT_STAGES:
                refused[identity] = refusal
            raise
        self._remembered = None if identity is None else (identity, world)
        return world


def _drop_tracebacks(refusal: BaseException) -> None:
    """Clear the traceback of a remembered refusal and of every exception it chains.

    A traceback holds the frames it unwound through, and a reader frame can
    hold the decompressed body; a memo that kept them would keep a whole save's
    body alive for as long as the file is unchanged. Re-raising a remembered
    refusal also APPENDS to its traceback, so clearing after every walk keeps
    it from growing call by call. The refusal's type, stage and cause type -
    all a remembered verdict is consulted for - are untouched.

    Args:
        refusal: The remembered refusal.
    """
    pending: list[BaseException] = [refusal]
    seen: set[int] = set()
    while pending:
        link = pending.pop()
        if id(link) in seen:
            continue
        seen.add(id(link))
        link.__traceback__ = None
        pending.extend(
            chained for chained in (link.__cause__, link.__context__) if chained is not None
        )


def _at_most_one(
    find_save: Callable[[Path | None], Path | None],
) -> Callable[[Path | None], tuple[Path, ...]]:
    """Adapt a one-save finder to the ranking the provider walks.

    Args:
        find_save: Picks one save or None.

    Returns:
        A ranking of that one save, or of none.
    """

    def ranked(account_dir: Path | None) -> tuple[Path, ...]:
        path = find_save(account_dir)
        return () if path is None else (path,)

    return ranked


def _identity(path: Path) -> tuple[Path, int, int] | None:
    """The identity a remembered world is keyed by, or None when unreadable.

    Args:
        path: The resolved newest save.

    Returns:
        (path, size in bytes, modification time in nanoseconds), or None when
        the file cannot be stat-ed - for example it vanished between the
        listing and here, which on a machine where the game is running is the
        ordinary case.
    """
    try:
        status = path.stat()
    except OSError:
        return None
    return (path, status.st_size, status.st_mtime_ns)


class InstalledRegistryProvider:
    """Hands up the normalized registry, or says there is no install.

    Satisfies ``contract.RegistryProvider[Registry]`` structurally, for the same
    reason and in the same direction as :class:`SaveWorldProvider`.
    """

    def __init__(
        self,
        *,
        find_install: Callable[[], tuple[Path | None, str]] = locate.resolve_game_dir,
        read_docs: Callable[[Path], str] = read_docs_text,
    ) -> None:
        """Wire the provider, defaulting to the real install resolution.

        Args:
            find_install: Returns (install directory or None, the resolution
                label that spoke). The label is discarded here: it can name an
                override that points inside a home directory.
            read_docs: Reads and decodes the shipped docs file.
        """
        self._find_install = find_install
        self._read_docs = read_docs

    def registry(self) -> Registry | None:
        """The normalized registry, or None when this machine has no install.

        THE RELATIVE PATH TO THE DOCS FILE IS NOT SPELLED HERE.
        ``clockspeed/data/version.py`` owns ``DOCS_RELATIVE_PARTS`` and this
        joins it, so a shipped layout change moves one literal rather than two.

        Returns:
            The registry, or None. None covers "no install found", "the docs
            file is absent or would not decode" and "the shipped grammar has
            changed" - the last of which is a real finding, but one the drift
            guard reports, not one a dashboard request should raise on.
        """
        try:
            install, _label = self._find_install()
        except OSError:
            return None
        if install is None:
            return None
        docs = install.joinpath(*version.DOCS_RELATIVE_PARTS)
        try:
            text = self._read_docs(docs)
        except (DocsExtractError, OSError, ValueError):
            return None
        try:
            return registry.build_registry(load_document(text))
        except (registry.RegistryError, DocsExtractError, ValueError):
            return None


def _wall_clock_seconds() -> int:
    """The current instant in whole seconds since the epoch - the default clock."""
    return int(time.time())


class StoreAdviceSource:
    """Runs the advisor over one world, reading both advice stores (CS-1270).

    Satisfies ``advice.AdviceSource`` structurally, in the same direction as
    :class:`SaveWorldProvider`.

    THE SURFACE DOES NOT COMPUTE HERE. :meth:`advice` hands the world and the
    registry to :func:`clockspeed.advisor.advise.advise_world`, which composes
    the audit models, runs the rules and resolves every card. No surface module
    imports ``clockspeed.audit``; the advisor is the layer that consumes it.

    :meth:`advice` ONLY READS. The ledger and the mute store are read whole in
    one open, and every writer replaces the file atomically, so a read never
    sees a half-written store - a GET never writes.

    :meth:`record` IS THE ONE WRITE (CS-1269), and it is the advisor's own
    ``Ledger.set_state`` or ``Ledger.snooze``: the surface hands over the world
    token, the card id and the kind, and the ledger decides whether a snooze
    ends after now. It is reached only through ``POST /api/advice/<id>/state``,
    which the server admits only with a same-origin proof. Mutes are not
    recorded here.

    THE CLOCK IS INJECTED and read once per call, only when advice is asked
    for; the default is the wall clock in whole seconds.

    NOT A DATACLASS, for the reason :class:`SaveWorldProvider` states: the store
    directory is a ``Path`` and a generated ``__repr__`` would render it.
    """

    def __init__(
        self,
        directory: Path | None = None,
        *,
        clock: Callable[[], int] = _wall_clock_seconds,
    ) -> None:
        """Wire the source to one store directory and one clock.

        Args:
            directory: Where both stores live, or None for the advisor's own
                default - the gitignored ``data/`` directory.
            clock: Answers the current instant. Never read at construction.
        """
        self._directory = directory
        self._clock = clock

    def advice(self, world: WorldModel, registry: Registry) -> Advice | None:
        """The advice for one world, or None when a store could not be read.

        Args:
            world: The world model the server holds.
            registry: The normalized registry.

        Returns:
            The advice, or None when either store is corrupt or unreadable -
            the endpoint answers that 503 rather than an empty listing.
        """
        try:
            return advise_world(
                world,
                registry,
                ledger=Ledger(self._directory),
                mutes=MuteStore(self._directory),
                now=self._clock(),
            )
        except StoreError:
            return None

    def record(self, world: WorldModel, card_id: str, kind: str, until: int | None) -> bool | None:
        """Record one card's state in the world's ledger.

        Args:
            world: The world the card was advised over. Its header token keys
                the ledger and goes nowhere else.
            card_id: A card id the current advice lists.
            kind: A state kind the endpoint has already checked.
            until: The snooze end instant for ``snoozed``, None otherwise.

        Returns:
            True when written; False when the ledger refused the value - a
            snooze that does not end after now, or a kind it does not know; None
            when the store could not be read or written, in which case it is
            left byte-for-byte unchanged.
        """
        ledger = Ledger(self._directory)
        try:
            if until is None:
                ledger.set_state(world.token, card_id, CardState(kind))
            else:
                ledger.snooze(world.token, card_id, until=until, now=self._clock())
        except StoreError:
            return None
        except (ValueError, TypeError):
            return False
        return True


class StaticAssets:
    """Reads the dashboard's own files, and only the ones it was told about.

    THE NAME SET IS SUPPLIED BY THE CALLER AND IS THE SECOND OF TWO INDEPENDENT
    GATES. The server resolves a request through a frozen three-entry table -
    there is no path resolution step for a traversal to survive - and then this
    class refuses any name outside the set that same table was built from. One
    literal table, two enforcement points: if the server is ever changed to hand
    over a request path, the path is not in the set and nothing is read.

    NOT A DATACLASS, for the reason :class:`SaveWorldProvider` states: the web
    directory is a ``Path`` and a generated ``__repr__`` would render it.
    """

    def __init__(self, web_dir: Path, names: Iterable[str]) -> None:
        """Wire the reader to one directory and one closed set of names.

        Args:
            web_dir: Where the assets live. NOT required to exist - the asset
                slice can land after this one, and a missing directory is a 404
                rather than a crash.
            names: Every filename this reader will ever open.
        """
        self._web_dir = web_dir
        self._names = frozenset(names)

    def asset(self, name: str) -> bytes | None:
        """The bytes of one named asset, or None when it cannot be served.

        Args:
            name: The filename, which must be one this reader was told about.

        Returns:
            The bytes, or None when the name is not in the closed set, carries a
            separator, or names something absent or unreadable. A single None
            for all four, because the caller renders the same 404 for each and a
            finer answer would only tell a caller which files exist.
        """
        if name not in self._names:
            return None
        if any(token in name for token in FORBIDDEN_IN_AN_ASSET_NAME):
            return None
        try:
            return (self._web_dir / name).read_bytes()
        except OSError:
            return None
