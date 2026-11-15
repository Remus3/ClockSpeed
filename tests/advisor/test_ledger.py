"""CS-500 - the per-world ledger and the global per-rule mute store.

BOOTSTRAP.md section 5.2 and CLAUDE.md section 7: two persistence layers, two
SEPARATE files, the ledger keyed by the save header's world token and an unseen
token treated as a new world rather than a failure. Every token here is an
invented 22-character base64url literal; no real save data is read.

The world token is personal data. Assertions that grade its absence bind the
verdict to a scalar first, so a failure renders a boolean and never the
rendering that carried the token.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from pathlib import Path

import pytest

from clockspeed.advisor import ledger as ledger_mod
from clockspeed.advisor.ledger import (
    LEDGER_FILENAME,
    MUTES_FILENAME,
    SCHEMA_VERSION,
    CardState,
    Ledger,
    MuteStore,
    StoreCorruptError,
    StoreError,
    StoreWriteError,
    WorldTokenError,
    default_store_dir,
    world_key,
)
from tests import conftest

# Invented, synthetic, and shaped like the real thing (BOOTSTRAP.md section 2.4).
TOKEN_A = "AAAAsyntheticTokenAAAA"  # noqa: S105 - a synthetic world token, not a secret
TOKEN_B = "BBBBsyntheticTokenBBBB"  # noqa: S105 - a synthetic world token, not a secret
TOKEN_LENGTH = 22
SHA256_HEX_LENGTH = 64
VERSION_TWO = 2  # CS-1268: stores a shown new card and its rule
VERSION_THREE = 3  # CS-1246: stores the shown-and-deferred count the aging guard reads


def _chain_hidden(exc: BaseException) -> bool:
    """Whether a default traceback prints nothing of this error's chain.

    True when the error has no cause and no context at all, so the only
    text a traceback adds beyond the frames is the error's own message.
    """
    return exc.__cause__ is None and exc.__context__ is None


def test_the_synthetic_tokens_are_shaped_like_real_ones() -> None:
    assert len(TOKEN_A) == TOKEN_LENGTH
    assert len(TOKEN_B) == TOKEN_LENGTH


def test_an_unseen_world_token_is_a_new_world(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    assert not led.knows_world(TOKEN_A)
    assert led.state(TOKEN_A, "card-1", now=0) == CardState.new()
    led.set_state(TOKEN_A, "card-1", CardState.accepted())
    # A second, never-seen world on a store that already holds one.
    assert not led.knows_world(TOKEN_B)
    assert led.state(TOKEN_B, "card-1", now=0) == CardState.new()
    assert led.knows_world(TOKEN_A)
    assert led.state(TOKEN_A, "card-1", now=0) == CardState.accepted()


def test_ledger_and_mutes_are_separate_files(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    mutes = MuteStore(tmp_path)
    led.set_state(TOKEN_A, "card-1", CardState.pinned())
    ledger_bytes = (tmp_path / LEDGER_FILENAME).read_bytes()
    mutes.mute("power.headroom")
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted([LEDGER_FILENAME, MUTES_FILENAME])
    # Muting never touches the ledger, and the two hold disjoint content.
    assert (tmp_path / LEDGER_FILENAME).read_bytes() == ledger_bytes
    assert b"power.headroom" not in ledger_bytes
    assert b"card-1" not in (tmp_path / MUTES_FILENAME).read_bytes()
    mutes_bytes = (tmp_path / MUTES_FILENAME).read_bytes()
    led.set_state(TOKEN_A, "card-2", CardState.dismissed())
    assert (tmp_path / MUTES_FILENAME).read_bytes() == mutes_bytes
    # A mute is global: it holds for every world, seen or not.
    assert mutes.is_muted("power.headroom")
    assert not mutes.is_muted("nodes.claim")


def test_first_write_carries_schema_version(tmp_path: Path) -> None:
    Ledger(tmp_path).set_state(TOKEN_A, "card-1", CardState.completed())
    MuteStore(tmp_path).mute("power.headroom")
    for name in (LEDGER_FILENAME, MUTES_FILENAME):
        doc = json.loads((tmp_path / name).read_bytes())
        assert doc["schema_version"] == SCHEMA_VERSION
    assert SCHEMA_VERSION == VERSION_THREE  # CS-1246


CORRUPT_PAYLOADS = [
    b"{not json",
    b"",
    b"[]",
    b'{"worlds": {}}',
    b'{"schema_version": 99, "worlds": {}, "rules": []}',
    b'{"schema_version": true, "worlds": {}, "rules": []}',
    b'{"schema_version": 1, "worlds": [], "rules": {}}',
    b'{"schema_version": 1, "worlds": {"k": {"c": {"state": "bogus"}}}, "rules": 3}',
    b"\xff\xfe\x00",
]


@pytest.mark.parametrize("payload", CORRUPT_PAYLOADS)
def test_a_corrupt_store_is_refused_and_unchanged(tmp_path: Path, payload: bytes) -> None:
    for name in (LEDGER_FILENAME, MUTES_FILENAME):
        (tmp_path / name).write_bytes(payload)
    led = Ledger(tmp_path)
    mutes = MuteStore(tmp_path)
    with pytest.raises(StoreCorruptError):
        led.state(TOKEN_A, "card-1", now=0)
    with pytest.raises(StoreCorruptError):
        led.set_state(TOKEN_A, "card-1", CardState.accepted())
    with pytest.raises(StoreCorruptError):
        mutes.is_muted("power.headroom")
    with pytest.raises(StoreCorruptError):
        mutes.mute("power.headroom")
    for name in (LEDGER_FILENAME, MUTES_FILENAME):
        assert (tmp_path / name).read_bytes() == payload
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted([LEDGER_FILENAME, MUTES_FILENAME])


@pytest.mark.parametrize("version", ["99", "0", "true", '"1"', "1.0", "null"])
def test_an_unknown_schema_version_is_refused_and_unchanged(tmp_path: Path, version: str) -> None:
    # Each payload is otherwise the exact shape its store writes, so only the
    # version check can refuse it.
    ledger_payload = ('{"schema_version": ' + version + ', "worlds": {}}').encode("ascii")
    mutes_payload = ('{"rules": [], "schema_version": ' + version + "}").encode("ascii")
    (tmp_path / LEDGER_FILENAME).write_bytes(ledger_payload)
    (tmp_path / MUTES_FILENAME).write_bytes(mutes_payload)
    with pytest.raises(StoreCorruptError):
        Ledger(tmp_path).set_state(TOKEN_A, "card-1", CardState.accepted())
    with pytest.raises(StoreCorruptError):
        MuteStore(tmp_path).mute("power.headroom")
    assert (tmp_path / LEDGER_FILENAME).read_bytes() == ledger_payload
    assert (tmp_path / MUTES_FILENAME).read_bytes() == mutes_payload


def test_the_version_one_shape_is_accepted_as_written_by_hand(tmp_path: Path) -> None:
    # Control for the arm above: the same payload at version 1 is read.
    (tmp_path / LEDGER_FILENAME).write_bytes(b'{"schema_version": 1, "worlds": {}}')
    (tmp_path / MUTES_FILENAME).write_bytes(b'{"rules": ["x.rule"], "schema_version": 1}')
    assert Ledger(tmp_path).state(TOKEN_A, "card-1", now=0) == CardState.new()
    assert MuteStore(tmp_path).is_muted("x.rule")


def test_a_valid_store_of_one_kind_is_corrupt_as_the_other(tmp_path: Path) -> None:
    MuteStore(tmp_path).mute("power.headroom")
    mutes_bytes = (tmp_path / MUTES_FILENAME).read_bytes()
    (tmp_path / LEDGER_FILENAME).write_bytes(mutes_bytes)
    with pytest.raises(StoreCorruptError):
        Ledger(tmp_path).state(TOKEN_A, "card-1", now=0)
    assert (tmp_path / LEDGER_FILENAME).read_bytes() == mutes_bytes


def test_no_token_in_repr_or_error(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    led.set_state(TOKEN_A, "card-1", CardState.accepted())
    renderings = [repr(led), str(led), repr(MuteStore(tmp_path))]
    renderings.extend(p.name for p in tmp_path.iterdir())
    renderings.append((tmp_path / LEDGER_FILENAME).read_text(encoding="ascii"))
    (tmp_path / LEDGER_FILENAME).write_bytes(b"{not json")
    with pytest.raises(StoreCorruptError) as corrupt:
        led.state(TOKEN_A, "card-1", now=0)
    with pytest.raises(ValueError, match="snooze") as bad_snooze:
        Ledger(tmp_path / "other").snooze(TOKEN_A, "card-1", until=5, now=5)
    renderings.extend(str(info.value) + repr(info.value) for info in (corrupt, bad_snooze))
    assert _chain_hidden(corrupt.value)
    joined = "\n".join(renderings)
    token_leaked = TOKEN_A in joined
    dir_leaked = str(tmp_path) in joined
    assert not token_leaked
    assert not dir_leaked
    # Positive control: the digest the store is keyed by IS present, so the
    # renderings above are the right ones to have searched.
    digest_present = world_key(TOKEN_A) in joined
    assert digest_present


def test_world_key_is_a_stable_digest_not_the_token() -> None:
    key = world_key(TOKEN_A)
    assert key == world_key(TOKEN_A)
    assert key != world_key(TOKEN_B)
    assert len(key) == SHA256_HEX_LENGTH
    assert all(c in "0123456789abcdef" for c in key)


@pytest.mark.parametrize(
    "bad",
    [
        "",
        5,
        None,
        b"AAAAsyntheticTokenAAAA",
        "AAAAsynthetic\ud800TokenAAA",
        "AAAAsynth\u00e9ticTokenAA",
    ],
)
def test_a_non_token_is_refused_with_a_fixed_store_error(bad: object) -> None:
    with pytest.raises(WorldTokenError) as info:
        world_key(bad)  # type: ignore[arg-type]
    assert isinstance(info.value, StoreError)
    fixed_args = info.value.args == (WorldTokenError.MESSAGE,)
    assert fixed_args
    assert info.value.__context__ is None
    assert info.value.__cause__ is None


def test_snooze_reads_the_injected_now_and_never_a_clock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _no_clock() -> float:
        raise AssertionError("the ledger read a clock")

    monkeypatch.setattr(time, "time", _no_clock)
    monkeypatch.setattr(time, "monotonic", _no_clock)
    led = Ledger(tmp_path)
    led.snooze(TOKEN_A, "card-1", until=100, now=10)
    assert led.state(TOKEN_A, "card-1", now=99) == CardState.snoozed(100)
    assert led.state(TOKEN_A, "card-1", now=100) == CardState.new()
    assert led.state(TOKEN_A, "card-1", now=500) == CardState.new()


@pytest.mark.parametrize(("until", "now"), [(5, 5), (4, 5), (1.5, 0), (True, 0), (5, 1.0)])
def test_a_snooze_that_is_not_in_the_future_or_not_an_int_is_refused(
    tmp_path: Path, until: object, now: object
) -> None:
    with pytest.raises((TypeError, ValueError)):
        Ledger(tmp_path).snooze(TOKEN_A, "card-1", until=until, now=now)  # type: ignore[arg-type]
    assert list(tmp_path.iterdir()) == []


def test_every_state_round_trips(tmp_path: Path) -> None:
    states = {
        "c-accepted": CardState.accepted(),
        "c-dismissed": CardState.dismissed(),
        "c-pinned": CardState.pinned(),
        "c-completed": CardState.completed(),
        "c-snoozed": CardState.snoozed(1000),
    }
    led = Ledger(tmp_path)
    for card_id, state in states.items():
        led.set_state(TOKEN_A, card_id, state)
    reread = Ledger(tmp_path)
    for card_id, state in states.items():
        assert reread.state(TOKEN_A, card_id, now=0) == state
    reread.set_state(TOKEN_A, "c-pinned", CardState.new())
    assert reread.state(TOKEN_A, "c-pinned", now=0) == CardState.new()
    assert "c-pinned" not in (tmp_path / LEDGER_FILENAME).read_text(encoding="ascii")


def test_card_state_kinds_are_the_bootstrap_six() -> None:
    expected = frozenset({"new", "accepted", "dismissed", "snoozed", "pinned", "completed"})
    assert expected == CardState.KINDS
    with pytest.raises(ValueError, match="unknown card state kind"):
        CardState("bogus")
    with pytest.raises(ValueError, match="until instant"):
        CardState("snoozed")
    with pytest.raises(ValueError, match="until instant"):
        CardState("pinned", until=5)


def test_unmute_and_the_muted_set(tmp_path: Path) -> None:
    mutes = MuteStore(tmp_path)
    assert mutes.muted() == frozenset()
    mutes.mute("b.rule")
    mutes.mute("a.rule")
    mutes.mute("a.rule")
    assert mutes.muted() == frozenset({"a.rule", "b.rule"})
    mutes.unmute("b.rule")
    mutes.unmute("never.muted")
    assert mutes.muted() == frozenset({"a.rule"})


def test_writes_are_deterministic_sorted_ascii_lf(tmp_path: Path) -> None:
    def build(directory: Path) -> tuple[bytes, bytes]:
        led = Ledger(directory)
        led.set_state(TOKEN_B, "z-card", CardState.pinned())
        led.set_state(TOKEN_A, "a-card", CardState.snoozed(7))
        mutes = MuteStore(directory)
        mutes.mute("z.rule")
        mutes.mute("a.rule")
        return (
            (directory / LEDGER_FILENAME).read_bytes(),
            (directory / MUTES_FILENAME).read_bytes(),
        )

    first = build(tmp_path / "one")
    second = build(tmp_path / "two")
    assert first == second
    for blob in first:
        assert b"\r" not in blob
        blob.decode("ascii")
        doc = json.loads(blob)
        assert json.dumps(doc, sort_keys=True, indent=2).encode("ascii") + b"\n" == blob
    assert json.loads(first[1])["rules"] == ["a.rule", "z.rule"]


def test_a_failed_rename_leaves_the_store_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    led = Ledger(tmp_path)
    led.set_state(TOKEN_A, "card-1", CardState.accepted())
    before = (tmp_path / LEDGER_FILENAME).read_bytes()

    def _refuse(_src: object, _dst: object) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(os, "replace", _refuse)
    monkeypatch.setattr(ledger_mod.time, "sleep", lambda _s: None)
    with pytest.raises(StoreWriteError):
        led.set_state(TOKEN_A, "card-1", CardState.dismissed())
    assert (tmp_path / LEDGER_FILENAME).read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == [LEDGER_FILENAME]


def test_a_failed_write_raises_no_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _refuse(_src: object, dst: object) -> None:
        raise PermissionError(13, "Access is denied", str(dst))

    monkeypatch.setattr(os, "replace", _refuse)
    monkeypatch.setattr(ledger_mod.time, "sleep", lambda _s: None)
    with pytest.raises(StoreWriteError) as info:
        MuteStore(tmp_path).mute("power.headroom")
    rendered = str(info.value) + repr(info.value)
    dir_leaked = str(tmp_path) in rendered
    assert not dir_leaked
    assert _chain_hidden(info.value)


def test_the_store_directory_is_created_on_first_write(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "store"
    Ledger(target).set_state(TOKEN_A, "card-1", CardState.accepted())
    assert (target / LEDGER_FILENAME).is_file()


def test_reading_never_creates_a_file(tmp_path: Path) -> None:
    Ledger(tmp_path).state(TOKEN_A, "card-1", now=0)
    MuteStore(tmp_path).is_muted("power.headroom")
    assert list(tmp_path.iterdir()) == []


def test_the_default_store_dir_is_the_gitignored_data_dir() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    assert default_store_dir() == repo_root / "data"
    assert Ledger().directory_is_default
    assert MuteStore().directory_is_default


# --- CS-500 S3 repair: the refuted findings, one arm each --------------------

DIGEST_A = "a" * 64
STALE_HEX = "0123456789abcdef"
HELD_LOCK_ATTEMPTS = 3
TEMP_NAME_DRAWS = 50


def _write_both(directory: Path, payload: bytes) -> None:
    for name in (LEDGER_FILENAME, MUTES_FILENAME):
        (directory / name).write_bytes(payload)


def _assert_both_refused_and_unchanged(directory: Path, payload: bytes) -> None:
    with pytest.raises(StoreCorruptError):
        Ledger(directory).set_state(TOKEN_A, "card-1", CardState.accepted())
    with pytest.raises(StoreCorruptError):
        MuteStore(directory).mute("power.headroom")
    for name in (LEDGER_FILENAME, MUTES_FILENAME):
        assert (directory / name).read_bytes() == payload


def test_deep_nesting_is_refused_as_corrupt_and_unchanged(tmp_path: Path) -> None:
    depth = 200_000
    payload = b"[" * depth + b"]" * depth
    _write_both(tmp_path, payload)
    _assert_both_refused_and_unchanged(tmp_path, payload)


def test_an_oversized_store_is_refused_and_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger_payload = b'{"schema_version": 1, "worlds": {}}'
    mutes_payload = b'{"rules": ["a.rule", "b.rule"], "schema_version": 1}'
    monkeypatch.setattr(ledger_mod, "MAX_STORE_BYTES", len(ledger_payload) - 1)
    (tmp_path / LEDGER_FILENAME).write_bytes(ledger_payload)
    (tmp_path / MUTES_FILENAME).write_bytes(mutes_payload)
    with pytest.raises(StoreCorruptError):
        Ledger(tmp_path).set_state(TOKEN_A, "card-1", CardState.accepted())
    with pytest.raises(StoreCorruptError):
        MuteStore(tmp_path).mute("power.headroom")
    assert (tmp_path / LEDGER_FILENAME).read_bytes() == ledger_payload
    assert (tmp_path / MUTES_FILENAME).read_bytes() == mutes_payload


def test_the_size_cap_is_sixteen_mebibytes() -> None:
    assert ledger_mod.MAX_STORE_BYTES == 16 * 1024 * 1024


@pytest.mark.parametrize(
    "payload",
    [
        b'{"schema_version": 1, "schema_version": 1, "worlds": {}}',
        (
            b'{"schema_version": 1, "worlds": {"' + DIGEST_A.encode() + b'": '
            b'{"c": {"state": "pinned"}, "c": {"state": "accepted"}}}}'
        ),
        (
            b'{"schema_version": 1, "worlds": {"'
            + DIGEST_A.encode()
            + b'": {}, "'
            + DIGEST_A.encode()
            + b'": {}}}'
        ),
    ],
)
def test_a_duplicate_key_is_refused_and_unchanged(tmp_path: Path, payload: bytes) -> None:
    (tmp_path / LEDGER_FILENAME).write_bytes(payload)
    with pytest.raises(StoreCorruptError):
        Ledger(tmp_path).set_state(TOKEN_A, "card-1", CardState.accepted())
    assert (tmp_path / LEDGER_FILENAME).read_bytes() == payload


def test_a_duplicate_rule_document_key_is_refused(tmp_path: Path) -> None:
    payload = b'{"rules": [], "rules": ["x"], "schema_version": 1}'
    (tmp_path / MUTES_FILENAME).write_bytes(payload)
    with pytest.raises(StoreCorruptError):
        MuteStore(tmp_path).mute("power.headroom")
    assert (tmp_path / MUTES_FILENAME).read_bytes() == payload


@pytest.mark.parametrize(
    "record",
    [
        b'{"state": "pinned", "until": null}',
        b'{"state": "pinned", "until": 5}',
        b'{"state": "snoozed", "until": null}',
        b'{"state": "snoozed"}',
    ],
)
def test_a_misplaced_until_is_refused_and_unchanged(tmp_path: Path, record: bytes) -> None:
    payload = (
        b'{"schema_version": 1, "worlds": {"' + DIGEST_A.encode() + b'": {"c": ' + record + b"}}}"
    )
    (tmp_path / LEDGER_FILENAME).write_bytes(payload)
    with pytest.raises(StoreCorruptError):
        Ledger(tmp_path).state(TOKEN_A, "card-1", now=0)
    with pytest.raises(StoreCorruptError):
        Ledger(tmp_path).set_state(TOKEN_A, "card-1", CardState.accepted())
    assert (tmp_path / LEDGER_FILENAME).read_bytes() == payload


@pytest.mark.parametrize("key", ["abc", "A" * 64, "g" * 64, "a" * 63, "a" * 65, TOKEN_A])
def test_a_world_key_that_is_not_a_digest_is_refused(tmp_path: Path, key: str) -> None:
    payload = b'{"schema_version": 1, "worlds": {"' + key.encode() + b'": {}}}'
    (tmp_path / LEDGER_FILENAME).write_bytes(payload)
    with pytest.raises(StoreCorruptError):
        Ledger(tmp_path).set_state(TOKEN_A, "card-1", CardState.accepted())
    assert (tmp_path / LEDGER_FILENAME).read_bytes() == payload


def test_a_digest_world_key_is_accepted(tmp_path: Path) -> None:
    # Control for the arm above: the same document with a digest key reads.
    payload = b'{"schema_version": 1, "worlds": {"' + DIGEST_A.encode() + b'": {}}}'
    (tmp_path / LEDGER_FILENAME).write_bytes(payload)
    assert Ledger(tmp_path).state(TOKEN_A, "card-1", now=0) == CardState.new()


def test_two_instances_interleaving_keep_both_cards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A reads, then pauses; B starts its own read-modify-write while A is
    # paused. Without a lock B reads the store before A has written and its
    # write then drops A's card.
    real_read = ledger_mod._read_doc  # noqa: SLF001 - the seam under test
    a_inside = threading.Event()
    calls = {"n": 0}
    guard = threading.Lock()

    def slow_first_read(target: Path, payload_key: str) -> object:
        with guard:
            calls["n"] += 1
            first = calls["n"] == 1
        result = real_read(target, payload_key)
        if first:
            a_inside.set()
            time.sleep(0.3)
        return result

    monkeypatch.setattr(ledger_mod, "_read_doc", slow_first_read)
    errors: list[BaseException] = []

    def write(card_id: str) -> None:
        try:
            Ledger(tmp_path).set_state(TOKEN_A, card_id, CardState.accepted())
        except BaseException as exc:
            errors.append(exc)

    a = threading.Thread(target=write, args=("card-a",))
    a.start()
    assert a_inside.wait(conftest.fleet_test_guard.budget(5))
    b = threading.Thread(target=write, args=("card-b",))
    b.start()
    a.join(conftest.fleet_test_guard.budget(10))
    b.join(conftest.fleet_test_guard.budget(10))
    assert errors == []
    reread = Ledger(tmp_path)
    assert reread.state(TOKEN_A, "card-a", now=0) == CardState.accepted()
    assert reread.state(TOKEN_A, "card-b", now=0) == CardState.accepted()


def test_threaded_writers_lose_nothing_silently(tmp_path: Path) -> None:
    attempted = [f"card-{i}" for i in range(12)]
    refused: list[str] = []
    other: list[BaseException] = []

    def write(card_id: str) -> None:
        try:
            Ledger(tmp_path).set_state(TOKEN_A, card_id, CardState.pinned())
        except StoreWriteError:
            refused.append(card_id)
        except BaseException as exc:
            other.append(exc)

    threads = [threading.Thread(target=write, args=(c,)) for c in attempted]
    for t in threads:
        t.start()
    for t in threads:
        t.join(conftest.fleet_test_guard.budget(30))
    assert other == []
    reread = Ledger(tmp_path)
    persisted = {c for c in attempted if reread.state(TOKEN_A, c, now=0) == CardState.pinned()}
    assert persisted == set(attempted) - set(refused)
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == [LEDGER_FILENAME]


def test_a_held_lock_refuses_the_write_loudly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    led = Ledger(tmp_path)
    led.set_state(TOKEN_A, "card-1", CardState.accepted())
    before = (tmp_path / LEDGER_FILENAME).read_bytes()
    lock = tmp_path / f".{LEDGER_FILENAME}.lock"
    lock.write_bytes(b"")
    sleeps: list[float] = []
    monkeypatch.setattr(ledger_mod, "_LOCK_ATTEMPTS", HELD_LOCK_ATTEMPTS)
    monkeypatch.setattr(ledger_mod.time, "sleep", sleeps.append)
    with pytest.raises(StoreWriteError) as info:
        led.set_state(TOKEN_A, "card-1", CardState.dismissed())
    assert info.value.__context__ is None
    assert len(sleeps) == HELD_LOCK_ATTEMPTS
    assert (tmp_path / LEDGER_FILENAME).read_bytes() == before
    # A fresh lock belongs to a live holder and is never ours to remove.
    assert lock.exists()


def test_a_stale_lock_left_by_a_killed_writer_is_broken(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    led = Ledger(tmp_path)
    led.set_state(TOKEN_A, "card-1", CardState.accepted())
    lock = tmp_path / f".{LEDGER_FILENAME}.lock"
    lock.write_bytes(b"99999\n")
    aged = time.time() - ledger_mod.LOCK_STALE_SECONDS - 60
    os.utime(lock, (aged, aged))
    monkeypatch.setattr(ledger_mod, "_LOCK_ATTEMPTS", HELD_LOCK_ATTEMPTS)
    monkeypatch.setattr(ledger_mod.time, "sleep", lambda _s: None)
    led.set_state(TOKEN_A, "card-1", CardState.dismissed())
    assert Ledger(tmp_path).state(TOKEN_A, "card-1", now=0) == CardState.dismissed()
    assert not lock.exists()


def test_the_stale_threshold_is_well_above_a_hold() -> None:
    assert ledger_mod.LOCK_STALE_SECONDS >= 30  # noqa: PLR2004 - the floor under test


def test_a_held_lock_records_its_holder_pid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[bytes] = []
    lock = tmp_path / f".{LEDGER_FILENAME}.lock"
    real_read = ledger_mod._read_doc  # noqa: SLF001 - the seam under test

    def peek(target: Path, payload_key: str) -> object:
        seen.append(lock.read_bytes())
        return real_read(target, payload_key)

    monkeypatch.setattr(ledger_mod, "_read_doc", peek)
    Ledger(tmp_path).set_state(TOKEN_A, "card-1", CardState.accepted())
    assert seen[0].split(b"\n")[0] == str(os.getpid()).encode("ascii")


def test_temp_names_are_unique_per_write_and_match_the_sweep(tmp_path: Path) -> None:
    target = tmp_path / LEDGER_FILENAME
    temp_path = ledger_mod._temp_path  # noqa: SLF001 - the seam under test
    names = {temp_path(target).name for _ in range(TEMP_NAME_DRAWS)}
    assert len(names) == TEMP_NAME_DRAWS
    pattern = ledger_mod._temp_pattern(LEDGER_FILENAME)  # noqa: SLF001 - the seam under test
    assert all(pattern.fullmatch(n) for n in names)
    # Thread id and pid are both in the name, not the pid alone.
    one = next(iter(names))
    assert f".{os.getpid()}.{threading.get_ident()}." in one


def test_stale_temp_files_are_swept_on_a_successful_write(tmp_path: Path) -> None:
    stale = tmp_path / f".{LEDGER_FILENAME}.11.22.{STALE_HEX}.tmp"
    not_ours = tmp_path / f".{LEDGER_FILENAME}.notours.tmp"
    other_store = tmp_path / f".{MUTES_FILENAME}.11.22.{STALE_HEX}.tmp"
    for p in (stale, not_ours, other_store):
        p.write_bytes(b"x")
    Ledger(tmp_path).set_state(TOKEN_A, "card-1", CardState.accepted())
    assert not stale.exists()
    assert not_ours.exists()
    assert other_store.exists()


def test_the_rename_retries_a_transient_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_replace = os.replace
    attempts = ledger_mod._RENAME_ATTEMPTS  # noqa: SLF001 - the bound under test
    failures = {"left": attempts - 1}
    sleeps: list[float] = []

    def flaky(src: object, dst: object) -> None:
        if failures["left"] > 0:
            failures["left"] -= 1
            raise PermissionError(13, "Access is denied")
        real_replace(src, dst)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "replace", flaky)
    monkeypatch.setattr(ledger_mod.time, "sleep", sleeps.append)
    Ledger(tmp_path).set_state(TOKEN_A, "card-1", CardState.accepted())
    assert Ledger(tmp_path).state(TOKEN_A, "card-1", now=0) == CardState.accepted()
    assert len(sleeps) == attempts - 1


def test_the_rename_gives_up_after_its_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    attempts = ledger_mod._RENAME_ATTEMPTS  # noqa: SLF001 - the bound under test
    calls = {"n": 0}

    def always(_src: object, _dst: object) -> None:
        calls["n"] += 1
        raise PermissionError(13, "Access is denied")

    monkeypatch.setattr(os, "replace", always)
    monkeypatch.setattr(ledger_mod.time, "sleep", lambda _s: None)
    with pytest.raises(StoreWriteError):
        Ledger(tmp_path).set_state(TOKEN_A, "card-1", CardState.accepted())
    assert calls["n"] == attempts


def test_fsync_precedes_the_rename(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    real_fsync = os.fsync
    real_replace = os.replace

    def spy_fsync(fd: int) -> None:
        events.append("fsync")
        real_fsync(fd)

    def spy_replace(src: object, dst: object) -> None:
        events.append("replace")
        real_replace(src, dst)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "fsync", spy_fsync)
    monkeypatch.setattr(os, "replace", spy_replace)
    MuteStore(tmp_path).mute("power.headroom")
    assert events == ["fsync", "replace"]


def test_store_errors_carry_no_context_and_no_cause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    caught: list[BaseException] = []
    (tmp_path / "bad").mkdir()
    (tmp_path / "bad" / LEDGER_FILENAME).write_bytes(b"{not json")
    with pytest.raises(StoreCorruptError) as corrupt:
        Ledger(tmp_path / "bad").state(TOKEN_A, "card-1", now=0)
    caught.append(corrupt.value)
    (tmp_path / "rec").mkdir()
    (tmp_path / "rec" / LEDGER_FILENAME).write_bytes(
        b'{"schema_version": 1, "worlds": {"' + DIGEST_A.encode() + b'": {"c": {"state": "x"}}}}'
    )
    with pytest.raises(StoreCorruptError) as record:
        Ledger(tmp_path / "rec").state(TOKEN_A, "card-1", now=0)
    caught.append(record.value)
    with pytest.raises(WorldTokenError) as token:
        world_key("")
    caught.append(token.value)

    def _refuse(_src: object, _dst: object) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(os, "replace", _refuse)
    with pytest.raises(StoreWriteError) as write:
        MuteStore(tmp_path / "w").mute("power.headroom")
    caught.append(write.value)
    with_context = [type(e).__name__ for e in caught if e.__context__ is not None]
    with_cause = [type(e).__name__ for e in caught if e.__cause__ is not None]
    assert with_context == []
    assert with_cause == []


def test_the_default_store_dir_uses_no_private_import() -> None:
    source = Path(ledger_mod.__file__).read_text(encoding="ascii")
    assert re.search(r"import\s+_\w+|import\s*\(?[^)\n]*\b_repo_root\b", source) is None
    assert "_repo_root" not in vars(ledger_mod)


# --- CS-1268: schema version 2 stores a shown ``new`` card and its rule -----------


def _v1(record: bytes) -> bytes:
    return (
        b'{"schema_version": 1, "worlds": {"' + DIGEST_A.encode() + b'": {"c": ' + record + b"}}}"
    )


def test_a_shown_new_card_is_stored_with_its_rule_at_the_current_schema(tmp_path: Path) -> None:
    Ledger(tmp_path).reconcile(TOKEN_A, firing={"c": "x.rule"}, settled=(), shown_new=("c",))
    doc = json.loads((tmp_path / LEDGER_FILENAME).read_bytes())
    assert (SCHEMA_VERSION, doc["schema_version"]) == (VERSION_THREE, VERSION_THREE)
    assert doc["worlds"][world_key(TOKEN_A)]["c"] == {"state": "new", "rule": "x.rule"}


def test_a_version_one_ledger_still_loads_and_is_rewritten_as_two(tmp_path: Path) -> None:
    # The name is docs/LEDGER.md's CS-1268 citation and stays; since CS-1246 the
    # rewrite lands at the CURRENT schema, version 3, which this arm asserts.
    (tmp_path / LEDGER_FILENAME).write_bytes(
        b'{"schema_version": 1, "worlds": {"'
        + world_key(TOKEN_A).encode()
        + b'": {"c": {"state": "accepted"}}}}'
    )
    assert Ledger(tmp_path).recorded(TOKEN_A) == (("c", CardState.accepted()),)
    Ledger(tmp_path).set_state(TOKEN_A, "d", CardState.pinned())
    doc = json.loads((tmp_path / LEDGER_FILENAME).read_bytes())
    assert doc["schema_version"] == VERSION_THREE
    assert Ledger(tmp_path).recorded(TOKEN_A) == (
        ("c", CardState.accepted()),
        ("d", CardState.pinned()),
    )


def test_a_version_one_mute_store_still_loads(tmp_path: Path) -> None:
    (tmp_path / MUTES_FILENAME).write_bytes(b'{"rules": ["x.rule"], "schema_version": 1}')
    assert MuteStore(tmp_path).is_muted("x.rule")


@pytest.mark.parametrize(
    "record", [b'{"state": "new"}', b'{"state": "accepted", "rule": "x.rule"}']
)
def test_a_version_one_ledger_carrying_a_version_two_record_is_corrupt(
    tmp_path: Path, record: bytes
) -> None:
    payload = _v1(record)
    (tmp_path / LEDGER_FILENAME).write_bytes(payload)
    with pytest.raises(StoreCorruptError):
        Ledger(tmp_path).recorded(TOKEN_A)
    assert (tmp_path / LEDGER_FILENAME).read_bytes() == payload


@pytest.mark.parametrize("rule", [b'""', b"3", b"null", b"[]"])
def test_a_malformed_rule_is_corrupt(tmp_path: Path, rule: bytes) -> None:
    payload = (
        b'{"schema_version": 2, "worlds": {"'
        + DIGEST_A.encode()
        + b'": {"c": {"state": "new", "rule": '
        + rule
        + b"}}}}"
    )
    (tmp_path / LEDGER_FILENAME).write_bytes(payload)
    with pytest.raises(StoreCorruptError):
        Ledger(tmp_path).recorded(TOKEN_A)
    assert (tmp_path / LEDGER_FILENAME).read_bytes() == payload


# --- CS-1246: schema version 3 stores a card's shown-and-deferred count ----------

DEFERRED_KEY = "deferred"
RULE_X = "x.rule"
TWICE_DEFERRED = 2  # three runs of one card: shown new once, then deferred twice
# The card that holds the top spot in every showing order below that wants a deferred
# card under it (CS-1246): the first id in ``shown`` is cleared, never aged, so a card
# only ages when something else leads. It is never in ``firing``, so it is never recorded.
LEADER = "lead"


def _versioned(version: int, record: bytes) -> bytes:
    """One world, one card ``c`` with ``record``, at ``version``."""
    return (
        b'{"schema_version": '
        + str(version).encode("ascii")
        + b', "worlds": {"'
        + world_key(TOKEN_A).encode("ascii")
        + b'": {"c": '
        + record
        + b"}}}"
    )


def _run(led: Ledger, *, firing: tuple[str, ...], shown: tuple[str, ...]) -> None:
    """One advice run in which every ``firing`` card is shown as ``new``."""
    led.reconcile(
        TOKEN_A,
        firing=dict.fromkeys(firing, RULE_X),
        settled=(RULE_X,),
        shown_new=firing,
        shown=shown,
    )


def test_a_deferred_card_ages_once_per_run_it_is_shown_and_still_firing(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    _run(led, firing=("c",), shown=(LEADER, "c"))
    assert dict(led.deferrals(TOKEN_A)) == {}
    _run(led, firing=("c",), shown=(LEADER, "c"))
    assert dict(led.deferrals(TOKEN_A)) == {"c": 1}
    _run(led, firing=("c",), shown=(LEADER, "c"))
    assert dict(led.deferrals(TOKEN_A)) == {"c": 2}
    # Firing but not shown this run: the player did not see it, so it does not age.
    _run(led, firing=("c",), shown=())
    assert dict(led.deferrals(TOKEN_A)) == {"c": 2}


def test_a_card_that_stops_firing_is_not_aged(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    _run(led, firing=("c", "d"), shown=(LEADER, "c", "d"))
    _run(led, firing=("c", "d"), shown=(LEADER, "c", "d"))
    # c stops firing but is still named as shown; only d, which fires, ages.
    _run(led, firing=("d",), shown=(LEADER, "c", "d"))
    assert dict(led.deferrals(TOKEN_A)) == {"c": 1, "d": 2}
    assert dict(led.recorded(TOKEN_A)) == {"c": CardState.completed(), "d": CardState.new()}


def test_the_top_card_is_cleared_not_aged(tmp_path: Path) -> None:
    """A card whose count reached 3 reads 0 once it leads the showing order."""
    led = Ledger(tmp_path)
    for _ in range(4):
        _run(led, firing=("c",), shown=(LEADER, "c"))
    assert dict(led.deferrals(TOKEN_A)) == {"c": 3}
    _run(led, firing=("c",), shown=("c",))
    assert dict(led.deferrals(TOKEN_A)) == {}
    # Cleared is not forgotten: the card is still recorded, and its count key is gone.
    assert dict(led.recorded(TOKEN_A)) == {"c": CardState.new()}
    doc = json.loads((tmp_path / LEDGER_FILENAME).read_bytes())
    assert DEFERRED_KEY not in doc["worlds"][world_key(TOKEN_A)]["c"]


def test_a_leader_with_no_record_invents_nothing(tmp_path: Path) -> None:
    """An id that leads ``shown`` with no recorded card leaves the store byte-identical."""
    led = Ledger(tmp_path)
    for _ in range(3):
        _run(led, firing=("c",), shown=(LEADER, "c"))
    before = (tmp_path / LEDGER_FILENAME).read_bytes()
    led.reconcile(TOKEN_A, firing={"ghost": RULE_X}, settled=(), shown_new=(), shown=("ghost",))
    assert (tmp_path / LEDGER_FILENAME).read_bytes() == before
    assert [cid for cid, _ in led.recorded(TOKEN_A)] == ["c"]
    # Leading a list that holds a recorded card still ages that card and records no leader.
    led.reconcile(
        TOKEN_A,
        firing={"ghost": RULE_X, "c": RULE_X},
        settled=(),
        shown_new=(),
        shown=("ghost", "c"),
    )
    assert [cid for cid, _ in led.recorded(TOKEN_A)] == ["c"]
    assert dict(led.deferrals(TOKEN_A)) == {"c": 3}


def test_the_showing_order_is_load_bearing(tmp_path: Path) -> None:
    """The same id set in two showing orders leaves two different count mappings."""
    counts = []
    for name, order in (("one", ("c", "d")), ("two", ("d", "c"))):
        led = Ledger(tmp_path / name)
        # Both cards recorded at zero and not shown, so the store starts identical.
        _run(led, firing=("c", "d"), shown=())
        _run(led, firing=("c", "d"), shown=order)
        counts.append(dict(led.deferrals(TOKEN_A)))
    # Only the card below the top one is passed over; swapping the order swaps who ages.
    assert counts == [{"d": 1}, {"c": 1}]
    assert counts[0] != counts[1]


def test_a_card_recorded_this_run_starts_at_zero(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    _run(led, firing=("c",), shown=("c",))
    assert [cid for cid, _ in led.recorded(TOKEN_A)] == ["c"]
    assert dict(led.deferrals(TOKEN_A)) == {}
    doc = json.loads((tmp_path / LEDGER_FILENAME).read_bytes())
    assert DEFERRED_KEY not in doc["worlds"][world_key(TOKEN_A)]["c"]


def test_a_shown_id_with_no_record_is_never_invented(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    led.reconcile(TOKEN_A, firing={"c": RULE_X}, settled=(), shown_new=(), shown=("c",))
    assert led.recorded(TOKEN_A) == ()
    assert not (tmp_path / LEDGER_FILENAME).exists()


def test_the_store_is_written_only_when_something_changed_with_shown(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    # Nothing recorded and nothing newly shown: no write, so no file at all.
    led.reconcile(TOKEN_A, firing={"c": RULE_X}, settled=(), shown_new=(), shown=())
    assert not (tmp_path / LEDGER_FILENAME).exists()
    # Shown and still firing but with no record: still nothing to write.
    led.reconcile(TOKEN_A, firing={"c": RULE_X}, settled=(), shown_new=(), shown=("c",))
    assert not (tmp_path / LEDGER_FILENAME).exists()


def test_reconcile_keeps_its_return_shape_with_shown(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    _run(led, firing=("c",), shown=("c",))
    assert led.reconcile(
        TOKEN_A, firing={"c": RULE_X}, settled=(RULE_X,), shown_new=("c",), shown=("c",)
    ) == ((), ())
    assert led.reconcile(TOKEN_A, firing={}, settled=(RULE_X,), shown_new=(), shown=("c",)) == (
        ("c",),
        (),
    )


@pytest.mark.parametrize("bad", ["", 3, None])
def test_a_bad_shown_id_is_refused(tmp_path: Path, bad: object) -> None:
    with pytest.raises(ValueError, match="card id"):
        Ledger(tmp_path).reconcile(
            TOKEN_A,
            firing={"c": RULE_X},
            settled=(),
            shown_new=(),
            shown=(bad,),  # type: ignore[arg-type]
        )


def test_set_state_resets_the_count(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    for _ in range(3):
        _run(led, firing=("c", "d"), shown=(LEADER, "c", "d"))
    assert dict(led.deferrals(TOKEN_A)) == {"c": 2, "d": 2}
    led.set_state(TOKEN_A, "c", CardState.accepted())
    # Another card's count survives the read-modify-write; the player-touched one resets.
    assert dict(led.deferrals(TOKEN_A)) == {"d": 2}
    assert dict(led.recorded(TOKEN_A))["c"] == CardState.accepted()
    # The card's rule is still kept, as before.
    doc = json.loads((tmp_path / LEDGER_FILENAME).read_bytes())
    assert doc["worlds"][world_key(TOKEN_A)]["c"] == {"state": "accepted", "rule": RULE_X}


def test_recording_new_forgets_the_count_with_the_card(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    for _ in range(2):
        _run(led, firing=("c",), shown=("c",))
    led.set_state(TOKEN_A, "c", CardState.new())
    assert dict(led.deferrals(TOKEN_A)) == {}
    _run(led, firing=("c",), shown=("c",))
    assert dict(led.deferrals(TOKEN_A)) == {}


def test_a_reopened_card_starts_over(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    for _ in range(3):
        _run(led, firing=("c",), shown=(LEADER, "c"))
    assert dict(led.deferrals(TOKEN_A)) == {"c": 2}
    _run(led, firing=(), shown=())
    assert dict(led.recorded(TOKEN_A)) == {"c": CardState.completed()}
    # It fires again and is shown in the very run that reopens it: a fresh start, not 3.
    completed, reopened = led.reconcile(
        TOKEN_A, firing={"c": RULE_X}, settled=(RULE_X,), shown_new=("c",), shown=(LEADER, "c")
    )
    assert (completed, reopened) == ((), ("c",))
    assert dict(led.deferrals(TOKEN_A)) == {}
    _run(led, firing=("c",), shown=(LEADER, "c"))
    assert dict(led.deferrals(TOKEN_A)) == {"c": 1}


def test_a_version_three_document_round_trips(tmp_path: Path) -> None:
    payload = _versioned(3, b'{"state": "new", "rule": "x.rule", "deferred": 4}')
    (tmp_path / LEDGER_FILENAME).write_bytes(payload)
    led = Ledger(tmp_path)
    assert dict(led.deferrals(TOKEN_A)) == {"c": 4}
    assert led.recorded(TOKEN_A) == (("c", CardState.new()),)
    # A write of some other card carries the count through unchanged, as version 3.
    led.set_state(TOKEN_A, "d", CardState.pinned())
    doc = json.loads((tmp_path / LEDGER_FILENAME).read_bytes())
    assert doc["schema_version"] == VERSION_THREE
    assert doc["worlds"][world_key(TOKEN_A)]["c"] == {
        "state": "new",
        "rule": RULE_X,
        DEFERRED_KEY: 4,
    }
    assert dict(Ledger(tmp_path).deferrals(TOKEN_A)) == {"c": 4}


def test_a_version_two_ledger_is_read_with_zero_counts_and_rewritten_as_three(
    tmp_path: Path,
) -> None:
    (tmp_path / LEDGER_FILENAME).write_bytes(_versioned(2, b'{"state": "new", "rule": "x.rule"}'))
    led = Ledger(tmp_path)
    assert dict(led.deferrals(TOKEN_A)) == {}
    led.set_state(TOKEN_A, "d", CardState.pinned())
    doc = json.loads((tmp_path / LEDGER_FILENAME).read_bytes())
    assert doc["schema_version"] == VERSION_THREE


def test_a_document_with_no_deferrals_differs_from_version_two_only_by_its_version(
    tmp_path: Path,
) -> None:
    led = Ledger(tmp_path)
    led.set_state(TOKEN_A, "a", CardState.snoozed(9))
    led.set_state(TOKEN_A, "b", CardState.pinned())
    _run(led, firing=("c",), shown=("c",))
    written = (tmp_path / LEDGER_FILENAME).read_bytes()
    as_two = written.replace(b'"schema_version": 3', b'"schema_version": 2')
    assert as_two != written
    assert DEFERRED_KEY.encode("ascii") not in written
    # The version 2 rendering of the same document is read back identically.
    (tmp_path / "two").mkdir()
    (tmp_path / "two" / LEDGER_FILENAME).write_bytes(as_two)
    assert Ledger(tmp_path / "two").recorded(TOKEN_A) == led.recorded(TOKEN_A)


@pytest.mark.parametrize("version", [1, 2])
def test_an_older_version_carrying_the_count_is_corrupt_and_unchanged(
    tmp_path: Path, version: int
) -> None:
    record = b'{"state": "pinned", "deferred": 1}'
    if version == VERSION_TWO:
        record = b'{"state": "new", "rule": "x.rule", "deferred": 1}'
    payload = _versioned(version, record)
    (tmp_path / LEDGER_FILENAME).write_bytes(payload)
    with pytest.raises(StoreCorruptError):
        Ledger(tmp_path).deferrals(TOKEN_A)
    with pytest.raises(StoreCorruptError):
        Ledger(tmp_path).set_state(TOKEN_A, "d", CardState.pinned())
    with pytest.raises(StoreCorruptError):
        _run(Ledger(tmp_path), firing=("c",), shown=("c",))
    assert (tmp_path / LEDGER_FILENAME).read_bytes() == payload
    assert sorted(p.name for p in tmp_path.iterdir()) == [LEDGER_FILENAME]


@pytest.mark.parametrize(
    "count", [b"-1", b"0", b"true", b"false", b"1.0", b"2.5", b"null", b'"1"', b"[]"]
)
def test_a_malformed_count_is_corrupt_and_unchanged(tmp_path: Path, count: bytes) -> None:
    payload = _versioned(3, b'{"state": "new", "rule": "x.rule", "deferred": ' + count + b"}")
    (tmp_path / LEDGER_FILENAME).write_bytes(payload)
    with pytest.raises(StoreCorruptError):
        Ledger(tmp_path).deferrals(TOKEN_A)
    assert (tmp_path / LEDGER_FILENAME).read_bytes() == payload


def test_the_count_may_sit_on_a_snoozed_card(tmp_path: Path) -> None:
    payload = _versioned(3, b'{"state": "snoozed", "until": 5, "deferred": 2}')
    (tmp_path / LEDGER_FILENAME).write_bytes(payload)
    led = Ledger(tmp_path)
    assert dict(led.deferrals(TOKEN_A)) == {"c": 2}
    assert led.recorded(TOKEN_A) == (("c", CardState.snoozed(5)),)


def test_an_unseen_world_has_no_deferrals(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    assert dict(led.deferrals(TOKEN_A)) == {}
    for _ in range(2):
        _run(led, firing=("c",), shown=(LEADER, "c"))
    assert dict(led.deferrals(TOKEN_B)) == {}
    assert dict(led.deferrals(TOKEN_A)) == {"c": 1}
    # Reading creates nothing for the unseen world.
    assert not led.knows_world(TOKEN_B)


def test_deferrals_reads_no_clock_and_is_ordered_by_card_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    led = Ledger(tmp_path)
    for _ in range(2):
        _run(led, firing=("zz", "aa", "mm"), shown=(LEADER, "zz", "aa", "mm"))

    def no_clock() -> float:
        raise AssertionError("deferrals read the clock")

    monkeypatch.setattr(time, "time", no_clock)
    assert list(led.deferrals(TOKEN_A)) == ["aa", "mm", "zz"]


def test_deferrals_answers_a_fresh_immutable_mapping(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    for _ in range(2):
        _run(led, firing=("c",), shown=(LEADER, "c"))
    answer = led.deferrals(TOKEN_A)
    with pytest.raises(TypeError):
        answer["c"] = 99  # type: ignore[index]
    assert dict(led.deferrals(TOKEN_A)) == {"c": 1}


def test_deferrals_is_deterministic_over_the_same_store(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    for _ in range(3):
        _run(led, firing=("b", "a"), shown=(LEADER, "b", "a"))
    assert led.deferrals(TOKEN_A) == led.deferrals(TOKEN_A)
    assert list(led.deferrals(TOKEN_A).items()) == [("a", 2), ("b", 2)]


def test_two_identical_runs_write_identical_bytes(tmp_path: Path) -> None:
    def build(directory: Path) -> bytes:
        led = Ledger(directory)
        for _ in range(3):
            _run(led, firing=("z", "a"), shown=("z", "a"))
        led.set_state(TOKEN_A, "m", CardState.snoozed(7))
        return (directory / LEDGER_FILENAME).read_bytes()

    first = build(tmp_path / "one")
    second = build(tmp_path / "two")
    assert first == second
    assert b"\r" not in first
    first.decode("ascii")
    assert json.dumps(json.loads(first), sort_keys=True, indent=2).encode("ascii") + b"\n" == first
    assert json.loads(first)["worlds"][world_key(TOKEN_A)]["a"][DEFERRED_KEY] == TWICE_DEFERRED


def test_no_token_reaches_the_count_surface(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    for _ in range(2):
        _run(led, firing=("c",), shown=("c",))
    renderings = [repr(led.deferrals(TOKEN_A)), (tmp_path / LEDGER_FILENAME).read_text("ascii")]
    renderings.extend(p.name for p in tmp_path.iterdir())
    leaked = any(TOKEN_A in text for text in renderings)
    assert not leaked


# --- CS-1376: the closed snooze durations -------------------------------------

#: Spellings no token owns: case, padding, a bare number, an inherited member name.
OFF_MAPPING_TOKENS = ("", "1H", " 1h", "1h ", "3600", "0h", "forever", "constructor", "__len__")

#: The injected instant a duration is added to. A literal, never a clock.
SNOOZE_NOW = 1_000


def test_the_snooze_durations_are_a_closed_mapping_of_tokens_to_positive_whole_seconds() -> None:
    durations = ledger_mod.SNOOZE_DURATIONS
    held = len(durations)
    assert held >= 1
    bad_keys = [key for key in durations if type(key) is not str or not key or not key.isascii()]
    assert bad_keys == []
    bad_values = [
        key for key, seconds in durations.items() if type(seconds) is not int or seconds < 1
    ]
    assert bad_values == []


def test_the_snooze_durations_cannot_be_widened_in_place() -> None:
    refused = False
    try:
        ledger_mod.SNOOZE_DURATIONS["zqxj"] = 1  # type: ignore[index]
    except TypeError:
        refused = True
    assert refused


def test_a_token_resolves_to_the_injected_instant_plus_its_seconds() -> None:
    durations = ledger_mod.SNOOZE_DURATIONS
    assert len(durations) >= 1, "no token is published, so nothing below was resolved"
    wrong = [
        token
        for token, seconds in durations.items()
        if ledger_mod.snooze_end(token, now=SNOOZE_NOW) != SNOOZE_NOW + seconds
    ]
    assert wrong == []


def test_a_resolved_snooze_ends_after_now_and_the_ledger_takes_it(tmp_path: Path) -> None:
    token = next(iter(ledger_mod.SNOOZE_DURATIONS), None)
    assert token is not None
    until = ledger_mod.snooze_end(token, now=SNOOZE_NOW)
    assert until is not None
    Ledger(tmp_path).snooze(TOKEN_A, "c", until=until, now=SNOOZE_NOW)
    assert Ledger(tmp_path).state(TOKEN_A, "c", now=SNOOZE_NOW) == CardState.snoozed(until)


@pytest.mark.parametrize("token", OFF_MAPPING_TOKENS)
def test_a_token_off_the_mapping_resolves_to_nothing(token: str) -> None:
    # THE CONTROL: a token on the mapping does resolve, so None is the refusal and not a
    # function that answers None for everything.
    published = next(iter(ledger_mod.SNOOZE_DURATIONS), None)
    assert published is not None
    assert ledger_mod.snooze_end(published, now=SNOOZE_NOW) is not None
    assert ledger_mod.snooze_end(token, now=SNOOZE_NOW) is None


@pytest.mark.parametrize("now", [True, 1.5, "1000", None])
def test_a_clock_that_is_not_a_whole_instant_is_refused(now: object) -> None:
    published = next(iter(ledger_mod.SNOOZE_DURATIONS), None)
    assert published is not None
    with pytest.raises(TypeError):
        ledger_mod.snooze_end(published, now=now)  # type: ignore[arg-type]
