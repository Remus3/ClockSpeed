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
    StoreWriteError,
    default_store_dir,
    world_key,
)

# Invented, synthetic, and shaped like the real thing (BOOTSTRAP.md section 2.4).
TOKEN_A = "AAAAsyntheticTokenAAAA"  # noqa: S105 - a synthetic world token, not a secret
TOKEN_B = "BBBBsyntheticTokenBBBB"  # noqa: S105 - a synthetic world token, not a secret
TOKEN_LENGTH = 22
SHA256_HEX_LENGTH = 64


def _chain_hidden(exc: BaseException) -> bool:
    """Whether a default traceback prints nothing of this error's chain.

    True when the raise set no cause and suppressed its context, so the only
    text a traceback adds beyond the frames is the error's own message.
    """
    return exc.__cause__ is None and exc.__suppress_context__


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
    assert SCHEMA_VERSION == 1


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


@pytest.mark.parametrize("bad", ["", 5, None, b"AAAAsyntheticTokenAAAA"])
def test_a_non_token_is_refused(bad: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        world_key(bad)  # type: ignore[arg-type]


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
