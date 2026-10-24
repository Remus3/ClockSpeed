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
from clockspeed.data.docs_extract import DocsExtractError, load_document
from clockspeed.save import sightings, workdir
from clockspeed.save.world import (
    READER_REFUSAL_TYPES,
    SAVE_VERDICT_STAGES,
    STAGE_HEADER,
    WorldLoadError,
    WorldModel,
    load_newest_world,
    load_world,
    read_world_digest,
    refuse_again,
    world_digest,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence
    from pathlib import Path

    from clockspeed.advisor.advise import Advice
    from clockspeed.data.registry import Registry

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
    newer saves it skipped on the world it hands up, and falls back only to
    the refused newest save's own world when that world is known.

    ONLY A VERDICT ON THE SAVE'S OWN BYTES IS REMEMBERED, AND ONLY AS TWO
    WORDS. A refusal at a stage in ``world.SAVE_VERDICT_STAGES`` is kept by the
    same identity a world is, because the same bytes draw the same verdict: an
    unchanged refused save is not copied and parsed again on every probe, and a
    rewritten one is tried afresh. What is kept is the stage and the cause
    type, each the vocabulary's own string - NEVER the refusal object, whose
    suppressed context can hold the very bytes the reader failed to decode
    (CS-1309 F-A). A later walk meets the verdict as a fresh refusal raised by
    ``world.refuse_again``, with no cause and no context. A failure at any
    other stage - the copy, which is the environment, and the property map,
    which is the install - is never remembered and never falls back, so the
    next call tries the newest save again.

    WHAT ``identify`` READ IS REMEMBERED THE SAME WAY, AS A DIGEST. Which
    world a save's header names is kept by identity, so the walk's same-world
    check copies a save's header at most once per identity. What is kept is
    ``world.world_digest`` of the token - the ledger's own key - NEVER the
    token (CS-1309 r3): a memo of raw tokens rendered one per identified save
    through ``vars``, and a digest answers "the same world?" exactly as well.
    The remembered world still holds its token, as every world does; its own
    ``repr`` masks it.

    MERGED, NEVER REPLACED; BOUNDED BY THE RANKING (CS-1309 F1). Every walk
    adds to the memory and then prunes it to the files in the CURRENT ranking
    whose identity is unchanged - verdicts, digests and the remembered world
    alike. A walk that ends early, on a busy save or an unreadable mapping,
    therefore keeps every verdict it never reached, and a file gone from the
    ranking is forgotten, so the memory never outgrows the ranking.

    THE RESIDUAL, NAMED: a rewrite that keeps the same path, the same size and
    the same nanosecond modification time keeps the identity, so a refusal or
    a world digest - like a world - is served from memory until the file
    changes again or the process restarts. An ordinary write moves the
    modification time on NTFS; reaching this takes a deliberate restore.

    ONE MEMORY OUTLIVES THE RANKING ON PURPOSE: THE SIGHTING HISTORY (CS-1240).
    Every world :meth:`world` hands up is observed into a
    ``clockspeed.save.sightings.SightingHistory`` - which distinct saves of
    each world were read, and the first of them that carried each unmodelled
    class - and :meth:`sighting_history` hands it to the world endpoint. It is
    the only thing here NOT pruned to the ranking, because "first seen" is a
    claim about every save read since the server started, a file gone from the
    ranking included. It is held in memory only, never written (the CS-1240
    adjudication: a persistent one would make a GET write), so a restart
    forgets it. It holds digests, ordinals and class paths and never a path;
    the save layer merges it, and nothing here counts or compares. It grows by
    one small entry per distinct save read, which is what remembering every
    save read costs.

    THE FRAME HOLDS SAVE PATHS, AS IT ALWAYS HAS. :meth:`world` holds the
    ranking in a local for the walk and the prune, as the single-save version
    held the newest path; ``tests/locals_rendering_guard.py`` grades test
    frames at an assert and not this one. Every documented failure returns
    None inside the method, so only an undocumented exception type unwinds
    through the frame, and the suite's report redactor rewrites home paths.
    """

    def __init__(
        self,
        account_dir: Path | None = None,
        *,
        find_save: Callable[[Path | None], Path | None] | None = None,
        find_saves: Callable[[Path | None], Sequence[Path]] | None = None,
        load: Callable[[Path], WorldModel] = load_world,
        identify: Callable[[Path], str | None] = read_world_digest,
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
            identify: Answers which world a save's header names, as
                ``world.read_world_digest`` does - a digest, ``world.NO_WORLD``
                or None when unread.

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
        self._identify = identify
        self._lock = threading.Lock()
        self._remembered: tuple[tuple[Path, int, int], WorldModel] | None = None
        self._verdicts: dict[tuple[Path, int, int], tuple[str, str]] = {}
        self._digests: dict[tuple[Path, int, int], str] = {}
        self._sightings = sightings.EMPTY_HISTORY

    def sighting_history(self) -> sightings.SightingHistory:
        """Every save read since this provider was built, as the save layer keys it.

        A reference read of an immutable value, so it takes no lock: a caller
        racing a :meth:`world` call sees the history before or after that
        save was observed, never half of it.

        Returns:
            The history - ``sightings.EMPTY_HISTORY`` before the first read.
        """
        return self._sightings

    def world(self) -> WorldModel | None:
        """The current world, or None when this machine has no save to read.

        Returns:
            The world model, or None. None covers all three of "no save
            directory", "an empty save directory" and "no save that would
            parse" - the endpoint tells the first two from the third through the
            reason it picks, not through an exception it has to catch. A world
            read from an older save past a refused newer one carries a
            ``WARN_NEWER_SAVE_REFUSED`` or ``WARN_NEWEST_SAVE_UNIDENTIFIED``
            flag for what was skipped.

        A save whose identity - path, size, modification time - matches the
        last successful load is handed up without being copied or parsed
        again, and one matching a remembered verdict on its bytes is skipped
        without being copied or parsed again. Any other failed load is never
        remembered, so the next call retries it; a save whose identity cannot
        be read is loaded per call, exactly as before this provider remembered
        anything.

        Every world handed up is observed into :meth:`sighting_history`;
        observing a save already read changes nothing (CS-1240).
        """
        with self._lock:
            try:
                candidates = tuple(self._find_saves(self._account_dir))
            except OSError:
                return None
            try:
                if not candidates:
                    return None
                model = load_newest_world(
                    candidates, load=self._remembering_load, identify=self._remembering_identify
                )
            except (WorldLoadError, OSError, ValueError):
                return None
            finally:
                self._keep_ranked(candidates)
            # Only a world model is observed. The injectable load is typed to
            # return one; a test double standing in for a world is not one, and
            # has no header or object table to observe.
            if isinstance(model, WorldModel):
                self._sightings = sightings.observe(self._sightings, model)
            return model

    def _remembering_load(self, path: Path) -> WorldModel:
        """Load one candidate, answering from memory when its identity allows.

        Called with the lock held, once per candidate the walk loads, and never
        while an exception is in flight - so a remembered verdict is raised with
        no context.

        Args:
            path: The candidate.

        Returns:
            The remembered or freshly loaded world.

        Raises:
            WorldLoadError: The reader refused the save, now - the reader's own
                refusal - or, for an unchanged identity, on an earlier call -
                a fresh refusal rebuilt from the remembered two words; or the
                load failed for a reason that is no verdict on the bytes, which
                is never remembered.
        """
        identity = _identity(path)
        if identity is not None:
            verdict = self._verdicts.get(identity)
            if verdict is not None:
                refuse_again(*verdict)
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
            words = _verdict_words(refusal)
            if identity is not None and words is not None:
                self._verdicts[identity] = words
            raise
        self._remembered = None if identity is None else (identity, world)
        return world

    def _remembering_identify(self, path: Path) -> str | None:
        """Which world a candidate's header names, from memory when its identity allows.

        Called with the lock held, by the walk only once the newest save was
        refused after its header. Three shortcuts, each saving a copy of the
        save: a digest already read, a remembered verdict AT the header (that
        header will not read, so nothing is copied to learn so again), and
        the remembered world, which names its own world.

        Args:
            path: The candidate.

        Returns:
            The world's digest, ``world.NO_WORLD`` for a header naming none,
            or None when the header was not read.
        """
        identity = _identity(path)
        if identity is not None:
            digest = self._digests.get(identity)
            if digest is not None:
                return digest
            verdict = self._verdicts.get(identity)
            if verdict is not None and verdict[0] == STAGE_HEADER:
                return None
            remembered = self._remembered
            if remembered is not None and remembered[0] == identity:
                return world_digest(remembered[1].token)
        digest = self._identify(path)
        if identity is not None and digest is not None:
            self._digests[identity] = digest
        return digest

    def _keep_ranked(self, candidates: Sequence[Path]) -> None:
        """Forget everything not about a ranked file with an unchanged identity.

        Args:
            candidates: The ranking this call walked.
        """
        current = {identity for identity in map(_identity, candidates) if identity is not None}
        self._verdicts = {key: words for key, words in self._verdicts.items() if key in current}
        self._digests = {key: digest for key, digest in self._digests.items() if key in current}
        if self._remembered is not None and self._remembered[0] not in current:
            self._remembered = None


def _read_docs_bytes(path: Path) -> bytes:
    """Read the docs file's raw bytes, read-only - the default byte reader.

    Args:
        path: The docs file.

    Returns:
        Its complete contents.

    Raises:
        OSError: The file could not be read.
    """
    return path.read_bytes()


def _verdict_words(refusal: WorldLoadError) -> tuple[str, str] | None:
    """A refusal's stage and cause type as the vocabulary's OWN strings, or None.

    The strings kept are the ones ``world`` spells, found by equality, so the
    memo can hold no object the refusal handed over - not even a ``str``
    subclass carrying something of its own. A refusal outside either
    vocabulary is not remembered at all.

    Args:
        refusal: The reader's refusal.

    Returns:
        (stage, cause type), or None when the stage is no verdict on the bytes
        or the cause type is not a reader's refusal class.
    """
    stages = [stage for stage in SAVE_VERDICT_STAGES if stage == refusal.stage]
    causes = [cause for cause in sorted(READER_REFUSAL_TYPES) if cause == refusal.cause_type]
    if not stages or not causes:
        return None
    return stages[0], causes[0]


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

    PROVENANCE IS PASSED THROUGH, NEVER COMPUTED HERE (CS-1315). By default the
    docs file is read as raw BYTES and handed to
    ``clockspeed.data.registry.build_registry_from_bytes``, which records their
    sha256 on ``Registry.source_sha256``; this class hashes nothing and
    compares nothing. The comparison with the pin is the audit's, reached
    through :class:`StoreAdviceSource`. A caller that injects a TEXT reader
    gets a registry with no byte source, which every card then names as
    unverified - never a silent match.
    """

    def __init__(
        self,
        *,
        find_install: Callable[[], tuple[Path | None, str]] = locate.resolve_game_dir,
        read_docs: Callable[[Path], str] | None = None,
        read_docs_bytes: Callable[[Path], bytes] = _read_docs_bytes,
    ) -> None:
        """Wire the provider, defaulting to the real install resolution.

        Args:
            find_install: Returns (install directory or None, the resolution
                label that spoke). The label is discarded here: it can name an
                override that points inside a home directory.
            read_docs: Reads and decodes the shipped docs file, as
                ``docs_extract.read_docs_text`` does. When given, it is used
                INSTEAD of ``read_docs_bytes``, and the registry carries no
                source hash. None, the default, reads bytes.
            read_docs_bytes: Reads the shipped docs file's raw bytes - the
                default path, whose registry carries their sha256.
        """
        self._find_install = find_install
        self._read_docs = read_docs
        self._read_docs_bytes = read_docs_bytes

    def registry(self) -> Registry | None:
        """The normalized registry, or None when this machine has no install.

        THE RELATIVE PATH TO THE DOCS FILE IS NOT SPELLED HERE.
        ``clockspeed/data/version.py`` owns ``DOCS_RELATIVE_PARTS`` and this
        joins it, so a shipped layout change moves one literal rather than two.

        Returns:
            The registry, or None. None covers "no install found", "the docs
            file is absent or would not decode" and "the shipped grammar has
            changed" - the last of which is a real finding, but one the drift
            guard reports, not one a dashboard request should raise on. Read
            as bytes, the registry carries their sha256 (CS-1315).
        """
        try:
            install, _label = self._find_install()
        except OSError:
            return None
        if install is None:
            return None
        docs = install.joinpath(*version.DOCS_RELATIVE_PARTS)
        if self._read_docs is not None:
            return self._registry_from_text(docs, self._read_docs)
        # ONLY what an install can cause, as the text path catches it since
        # b12396c (CS-1315 fix 1). The read: OSError (absent or unreadable)
        # and ValueError (a path the platform refuses, such as one carrying a
        # NUL), the read's own pair there; no DocsExtractError, as a raw read
        # decodes nothing. The build: RegistryError (the shipped grammar
        # moved), DocsExtractError (bytes that will not decode or parse) and
        # ValueError, the build's own three there. A TypeError is a bug in this
        # tree and RAISES - a None here is a confident "no install".
        try:
            raw = self._read_docs_bytes(docs)
        except (OSError, ValueError):
            return None
        try:
            return registry.build_registry_from_bytes(raw)
        except (registry.RegistryError, DocsExtractError, ValueError):
            return None

    @staticmethod
    def _registry_from_text(docs: Path, read_docs: Callable[[Path], str]) -> Registry | None:
        """Build from a decoded text - a registry with no byte source.

        Args:
            docs: The docs file.
            read_docs: The injected text reader.

        Returns:
            The registry, carrying no source hash, or None as :meth:`registry`
            answers it.
        """
        try:
            text = read_docs(docs)
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
    The one thing handed over beside them is the pin,
    ``clockspeed.data.version.GAME_CHANGELIST`` as it reads at call time, so
    every card on a save another build wrote names both builds (CS-1288), and
    ``clockspeed.data.version.DOCS_SHA256`` the same way, so every card priced
    from a registry built from other docs bytes - or from none - says so
    (CS-1315). Both are values read and passed on; nothing here compares them.

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
                pinned_changelist=version.GAME_CHANGELIST,
                pinned_docs_sha256=version.DOCS_SHA256,
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
