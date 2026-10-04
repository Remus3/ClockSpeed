"""The per-world advice ledger and the global per-rule mute store (CS-500).

BOOTSTRAP.md section 5.2 and CLAUDE.md section 7 settle the shape: TWO
persistence layers, held in TWO SEPARATE FILES, never merged.

- The per-world ledger maps ``card_id -> state`` for one world, keyed by the
  save header's world token - never by a save filename and never by a world
  name. A token the ledger has never seen is a NEW WORLD, never a failure.
- The global mute store holds the rule ids silenced across every world.

PERSONAL DATA. The world token is personal data (CLAUDE.md section 3, items 11
and 12). It is never written to disk, never placed in a file name, and never
rendered by a ``repr``, an error message or a log line. The ledger keys each
world by :func:`world_key`, a SHA-256 hex digest of the token. The store
directory is withheld from every rendering for the same reason - an injected
directory may sit under a home path.

TIME. A snooze carries an ``until`` instant, and every read that resolves a
snooze takes the current instant as an injected ``now``. This module never
reads a clock, so the same inputs always give the same state.

DURABILITY. Every write is atomic: the whole document is serialised to a
temporary file in the same directory and renamed over the target, so a reader
sees the old store or the new one and never a half-written file (CLAUDE.md
non-negotiable 5). JSON is written with sorted keys, ASCII only, LF only, so two
runs over the same state produce identical bytes.

CORRUPTION. A store that does not parse, or parses into anything other than the
exact shape this version writes, is REFUSED with :class:`StoreCorruptError` and
left byte-for-byte unchanged - a write never proceeds over a store it could not
read. Every document carries ``schema_version`` from its first write; only that
field ships here, and migration between versions belongs to CS-1253.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Final

from clockspeed.data.locate import _repo_root

#: The version every document this module writes carries from its first write.
SCHEMA_VERSION: Final = 1

#: The six card states of BOOTSTRAP.md section 5.2.
CARD_STATE_KINDS: Final = frozenset(
    {"new", "accepted", "dismissed", "snoozed", "pinned", "completed"}
)

#: The per-world ledger's file name. Fixed, and never derived from a token.
LEDGER_FILENAME: Final = "ledger.json"

#: The global per-rule mute store's file name. A separate file, by settlement.
MUTES_FILENAME: Final = "mutes.json"

# Windows lets a scanner or an indexer hold a handle on a just-closed file, and
# os.replace then fails with PermissionError. The retry is short and bounded.
_RENAME_ATTEMPTS: Final = 5
_RENAME_BACKOFF_SECONDS: Final = 0.05

_MSG_CORRUPT: Final = "the advice store is corrupt and was left unchanged"
_MSG_UNREADABLE: Final = "the advice store could not be read"
_MSG_UNWRITABLE: Final = "the advice store could not be written; it is unchanged"
_MSG_BAD_WORLD: Final = "a world token must be a non-empty str"
_MSG_BAD_KIND: Final = "unknown card state kind"
_MSG_BAD_UNTIL: Final = "a snoozed state needs an until instant and no other state carries one"
_MSG_BAD_INSTANT: Final = "an instant must be an int"
_MSG_NOT_FUTURE: Final = "a snooze must end after now"
_MSG_BAD_ID: Final = "a card id and a rule id must be non-empty str"


# --- errors -----------------------------------------------------------------


class StoreError(Exception):
    """Base for every error this module raises. Messages are constants."""


class StoreCorruptError(StoreError):
    """The store's bytes are not a document this version wrote. Unchanged."""


class StoreReadError(StoreError):
    """The store exists but could not be read."""


class StoreWriteError(StoreError):
    """The new document could not be put in place. The old store is unchanged."""


# --- identity -----------------------------------------------------------------


def world_key(token: str) -> str:
    """Return the digest a world is keyed by - never the token itself.

    Args:
        token: The save header's world token.

    Returns:
        The SHA-256 hex digest of the token's UTF-8 bytes.

    Raises:
        TypeError: The token is not a str.
        ValueError: The token is empty.
    """
    if not isinstance(token, str):
        raise TypeError(_MSG_BAD_WORLD)
    if not token:
        raise ValueError(_MSG_BAD_WORLD)
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def default_store_dir() -> Path:
    """Return the default store directory - the gitignored ``data/``."""
    return _repo_root() / "data"


def _check_id(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(_MSG_BAD_ID)
    return value


def _check_instant(value: object) -> int:
    # bool is an int subclass and a float is not exact; both are refused.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(_MSG_BAD_INSTANT)
    return value


# --- card state ---------------------------------------------------------------


class CardState:
    """One card's state: a kind from BOOTSTRAP.md 5.2 and, if snoozed, an until."""

    KINDS = CARD_STATE_KINDS

    __slots__ = ("kind", "until")

    def __init__(self, kind: str, until: int | None = None) -> None:
        """Build a state, refusing an unknown kind or a misplaced until.

        Args:
            kind: One of :attr:`KINDS`.
            until: The instant a snooze ends. Required for ``snoozed`` only.

        Raises:
            ValueError: The kind is unknown, or ``until`` is present on a kind
                that is not ``snoozed`` or absent on one that is.
        """
        if kind not in self.KINDS:
            raise ValueError(_MSG_BAD_KIND)
        if (kind == "snoozed") != (until is not None):
            raise ValueError(_MSG_BAD_UNTIL)
        if until is not None:
            _check_instant(until)
        self.kind = kind
        self.until = until

    @classmethod
    def new(cls) -> CardState:
        """Return the state of a card nothing has been recorded for."""
        return cls("new")

    @classmethod
    def accepted(cls) -> CardState:
        """Return the accepted state."""
        return cls("accepted")

    @classmethod
    def dismissed(cls) -> CardState:
        """Return the dismissed state."""
        return cls("dismissed")

    @classmethod
    def pinned(cls) -> CardState:
        """Return the pinned state."""
        return cls("pinned")

    @classmethod
    def completed(cls) -> CardState:
        """Return the completed state."""
        return cls("completed")

    @classmethod
    def snoozed(cls, until: int) -> CardState:
        """Return a snooze that ends at ``until``."""
        return cls("snoozed", until)

    def __eq__(self, other: object) -> bool:
        """Return whether two states share a kind and an until."""
        if not isinstance(other, CardState):
            return NotImplemented
        return (self.kind, self.until) == (other.kind, other.until)

    def __hash__(self) -> int:
        """Hash consistently with :meth:`__eq__`."""
        return hash((self.kind, self.until))

    def __repr__(self) -> str:
        """Render the kind and any until. A state carries no world identity."""
        if self.until is None:
            return f"CardState({self.kind!r})"
        return f"CardState({self.kind!r}, until={self.until!r})"

    def as_record(self) -> dict[str, object]:
        """Return the JSON record this state is stored as."""
        doc: dict[str, object] = {"state": self.kind}
        if self.until is not None:
            doc["until"] = self.until
        return doc

    @classmethod
    def from_record(cls, doc: object) -> CardState:
        """Rebuild a stored state, refusing any record this version never writes.

        Raises:
            StoreCorruptError: The record is not a stored state.
        """
        if not isinstance(doc, dict) or not set(doc) <= {"state", "until"}:
            raise StoreCorruptError(_MSG_CORRUPT)
        kind = doc.get("state")
        until = doc.get("until")
        if not isinstance(kind, str) or kind == "new":
            raise StoreCorruptError(_MSG_CORRUPT)
        if until is not None and (isinstance(until, bool) or not isinstance(until, int)):
            raise StoreCorruptError(_MSG_CORRUPT)
        try:
            return cls(kind, until)
        except (TypeError, ValueError):
            raise StoreCorruptError(_MSG_CORRUPT) from None


# --- the shared file mechanics -----------------------------------------------


def _serialise(doc: dict[str, object]) -> bytes:
    return json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=True).encode("ascii") + b"\n"


def _read_doc(target: Path, payload_key: str) -> dict[str, object] | None:
    """Read and shape-check one store. ``None`` means no store exists yet."""
    try:
        raw = target.read_bytes()
    except FileNotFoundError:
        return None
    except OSError:
        raise StoreReadError(_MSG_UNREADABLE) from None
    try:
        doc = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, ValueError):
        raise StoreCorruptError(_MSG_CORRUPT) from None
    if not isinstance(doc, dict) or set(doc) != {"schema_version", payload_key}:
        raise StoreCorruptError(_MSG_CORRUPT)
    version = doc["schema_version"]
    # bool and float compare equal to 1 but are not a version this wrote.
    if type(version) is not int or version != SCHEMA_VERSION:
        raise StoreCorruptError(_MSG_CORRUPT)
    return doc


def _rename_with_retry(tmp: Path, target: Path) -> None:
    """Rename ``tmp`` over ``target``, retrying a transient Windows lock briefly."""
    for _ in range(_RENAME_ATTEMPTS - 1):
        try:
            tmp.replace(target)
        except PermissionError:
            time.sleep(_RENAME_BACKOFF_SECONDS)
        else:
            return
    tmp.replace(target)


def _write_doc(target: Path, doc: dict[str, object]) -> None:
    """Put ``doc`` at ``target`` atomically: temp file, then rename."""
    data = _serialise(doc)
    tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        _rename_with_retry(tmp, target)
    except OSError:
        raise StoreWriteError(_MSG_UNWRITABLE) from None
    finally:
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)


class _Store:
    """A directory-backed store whose repr never renders the directory."""

    __slots__ = ("_directory", "directory_is_default")

    def __init__(self, directory: Path | None = None) -> None:
        self.directory_is_default = directory is None
        self._directory = default_store_dir() if directory is None else Path(directory)

    def __repr__(self) -> str:
        where = "default" if self.directory_is_default else "injected"
        return f"{type(self).__name__}(<{where} directory>)"


# --- the per-world ledger -----------------------------------------------------


class Ledger(_Store):
    """The per-world ledger: ``card_id -> CardState`` for each world token.

    Args:
        directory: Where the store lives. Defaults to :func:`default_store_dir`.
    """

    __slots__ = ()

    def _path(self) -> Path:
        return self._directory / LEDGER_FILENAME

    def _worlds(self) -> dict[str, dict[str, CardState]]:
        doc = _read_doc(self._path(), "worlds")
        if doc is None:
            return {}
        worlds = doc["worlds"]
        if not isinstance(worlds, dict):
            raise StoreCorruptError(_MSG_CORRUPT)
        out: dict[str, dict[str, CardState]] = {}
        for key, cards in worlds.items():
            if not isinstance(cards, dict):
                raise StoreCorruptError(_MSG_CORRUPT)
            out[key] = {_check_stored_id(cid): CardState.from_record(s) for cid, s in cards.items()}
        return out

    def _save(self, worlds: dict[str, dict[str, CardState]]) -> None:
        payload = {
            key: {cid: state.as_record() for cid, state in cards.items()}
            for key, cards in worlds.items()
            if cards
        }
        _write_doc(self._path(), {"schema_version": SCHEMA_VERSION, "worlds": payload})

    def knows_world(self, token: str) -> bool:
        """Return whether anything has been recorded for this world."""
        return world_key(token) in self._worlds()

    def state(self, token: str, card_id: str, *, now: int) -> CardState:
        """Return a card's state in a world, resolving a snooze against ``now``.

        An unseen world and an unseen card both answer ``new``. A snooze whose
        ``until`` is at or before ``now`` has lapsed and also answers ``new``.
        """
        key = world_key(token)
        _check_id(card_id)
        _check_instant(now)
        found = self._worlds().get(key, {}).get(card_id)
        if found is None:
            return CardState.new()
        if found.until is not None and found.until <= now:
            return CardState.new()
        return found

    def set_state(self, token: str, card_id: str, state: CardState) -> None:
        """Record a card's state in a world. Recording ``new`` forgets the card."""
        key = world_key(token)
        _check_id(card_id)
        if not isinstance(state, CardState):
            raise TypeError(_MSG_BAD_KIND)
        worlds = self._worlds()
        cards = worlds.setdefault(key, {})
        if state.kind == "new":
            cards.pop(card_id, None)
        else:
            cards[card_id] = state
        self._save(worlds)

    def snooze(self, token: str, card_id: str, *, until: int, now: int) -> None:
        """Snooze a card until ``until``, which must lie after the injected ``now``."""
        world_key(token)
        _check_id(card_id)
        if _check_instant(until) <= _check_instant(now):
            raise ValueError(_MSG_NOT_FUTURE)
        self.set_state(token, card_id, CardState.snoozed(until))


def _check_stored_id(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise StoreCorruptError(_MSG_CORRUPT)
    return value


# --- the global per-rule mute store ---------------------------------------------


class MuteStore(_Store):
    """The global per-rule mute: rule ids silenced across every world, forever.

    Args:
        directory: Where the store lives. Defaults to :func:`default_store_dir`.
    """

    __slots__ = ()

    def _path(self) -> Path:
        return self._directory / MUTES_FILENAME

    def muted(self) -> frozenset[str]:
        """Return every muted rule id."""
        doc = _read_doc(self._path(), "rules")
        if doc is None:
            return frozenset()
        rules = doc["rules"]
        if not isinstance(rules, list):
            raise StoreCorruptError(_MSG_CORRUPT)
        return frozenset(_check_stored_id(r) for r in rules)

    def is_muted(self, rule_id: str) -> bool:
        """Return whether a rule is muted."""
        return _check_id(rule_id) in self.muted()

    def _save(self, rules: frozenset[str]) -> None:
        _write_doc(self._path(), {"schema_version": SCHEMA_VERSION, "rules": sorted(rules)})

    def mute(self, rule_id: str) -> None:
        """Mute a rule across every world."""
        self._save(self.muted() | {_check_id(rule_id)})

    def unmute(self, rule_id: str) -> None:
        """Lift a rule's mute. Unmuting a rule that is not muted is a no-op write."""
        self._save(self.muted() - {_check_id(rule_id)})
