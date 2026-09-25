"""The lane refusal seam, graded end to end: `lanes.py` -> `run_cycle` -> the row.

A REFUSED ACQUIRE IS A DURABLE FACT. `run_cycle` turns a refusal dict built by
`ops/loop/lanes.py` into a cycle row, and `append_record` writes that row into
`ops/loop/reports/queue_loop.jsonl`, a file that outlives every session. Every
value copied out of the refusal dict is therefore a value copied off a LOCK
FILE this driver did not write into a file that keeps it.

CS-1014 grades the pid half of that copy, which had a correct guard and no arm.

No arm here spawns a process, sleeps or reads the live channel. The lock arms
take REAL lane locks, but only under `tmp_path`, and each proves its own lock is
gone before it returns.
"""

from __future__ import annotations

import ast
import contextlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# A PLAIN IMPORT, never importorskip: a missing driver is a COLLECTION error.
from ops.loop import lanes, queue_loop  # noqa: E402

#: A path SEGMENT planted where an account name would sit. A segment carries no
#: separator, so it survives every escaping a renderer can apply.
NEEDLE: Final = "cs1014-account-needle"

#: A PATH-SHAPED pid, synthetic and rooted at no real home directory. Built from
#: parts so no tracked byte spells a home path; `Path` gives it this platform's
#: separator, which is the shape a hand-edited or older lock file would carry.
PLANTED_PID: Final = str(Path("/") / "synthetic-home" / NEEDLE / "lanes" / "queue.lock")

#: The two refusal words, and so the two sites that render `(pid {pid})`.
REFUSAL_WORDS: Final = ("lane_held", "worktree_in_use")


class FakeClock:
    """A wall and a monotonic clock that advance only through `sleep`."""

    def __init__(self) -> None:
        """Start both clocks at fixed readings."""
        self.wall = 1_000_000.0
        self.mono = 0.0

    def time(self) -> float:
        """Wall time, for the row stamp."""
        return self.wall

    def monotonic(self) -> float:
        """Deadline time."""
        return self.mono

    def sleep(self, seconds: float) -> None:
        """Advance both clocks instead of blocking."""
        self.wall += float(seconds)
        self.mono += float(seconds)


def _stated_surface(_worktree: Any) -> dict[str, Any]:
    """A STATED channel fact, so no arm here reads `moon_sync_inbox/`."""
    return {"unread": 0, "names": [], "more": 0, "reason": ""}


def _never_launch(_lane: str, **_kw: Any) -> dict[str, Any]:
    """A refused cycle must never reach the launcher."""
    message = "a refused acquire reached the launcher"
    raise AssertionError(message)


def _refusing(word: str, **extra: Any):
    """An `acquire` seam that refuses every attempt with `word`."""
    payload: dict[str, Any] = {"ok": False, "refused": word, "holder": "queue-b", "pid": 99}
    payload.update(extra)
    return lambda _lane, **_kw: dict(payload)


def _cycle(acquire, worktree: str = "cs-lane-queue", **over: Any) -> dict[str, Any]:
    """Run ONE refused cycle through the real `run_cycle`, every other seam faked."""
    clock = FakeClock()
    seams: dict[str, Any] = {
        "acquire": acquire,
        "release": lambda _token, **_kw: True,
        "launch": _never_launch,
        "alive": lambda _pid: False,
        "proc_started": lambda _pid: 1.0,
        "stranger": lambda _pid, _started: False,
        "kill": lambda _pid: None,
        "acquire_retries": 1,
        "sleep": clock.sleep,
        "clock": clock.time,
        "monotonic": clock.monotonic,
        "worktree": worktree,
        "surface": _stated_surface,
        "emit": lambda _line: None,
    }
    seams.update(over)
    return queue_loop.run_cycle(1, **seams)


def _write_and_read_back(record: dict[str, Any], log: Path) -> str:
    """Write the row through the driver's own writer and return the FILE bytes."""
    queue_loop.append_record(record, log, hold=contextlib.nullcontext, emit=lambda _l: None)
    return log.read_bytes().decode("utf-8")


def _flatten(text: object) -> str:
    """Collapse every separator run and case-fold, so escaping cannot hide a leak.

    `repr` doubles a backslash and `json.dumps` doubles it again; a raw substring
    search for the planted value then never matches, which is an oracle blind
    to its subject. Searching for a SEGMENT after this collapse is not.
    """
    return re.sub(r"[\\/]+", "/", str(text)).casefold()


def _leaked(rendered: object, needle: str) -> bool:
    """Did `needle` survive into `rendered` under any escaping."""
    return _flatten(needle) in _flatten(rendered)


# ===========================================================================
# CS-1014 - a path-shaped pid never reaches `detail` or the written row
# ===========================================================================


@pytest.mark.parametrize("word", REFUSAL_WORDS)
def test_cs1014_the_plant_is_potent_when_the_pid_guard_is_removed(
    word: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE CONTROL: with the guard replaced by `return pid`, the plant LANDS.

    Without this, the arm below could pass because the planted value never
    travelled as far as the row at all - a refusal the driver did not read, a
    seam it did not call - and its silence would measure nothing. Replacing the
    guard with the identity function IS the `return pid` mutant, applied through
    the module attribute `run_cycle` resolves at call time, and it must put the
    needle into BOTH the detail and the bytes on disk, on BOTH render sites.
    """
    monkeypatch.setattr(queue_loop, "_holder_pid", lambda pid: pid)
    got = _cycle(_refusing(word, pid=PLANTED_PID))
    written = _write_and_read_back(got, tmp_path / "cycles.jsonl")

    assert got["outcome"] == word, "the plant did not ride the refusal it was planted on"
    assert _leaked(got["detail"], NEEDLE), f"the plant never reached detail on {word}"
    assert _leaked(written, NEEDLE), f"the plant never reached the written row on {word}"


@pytest.mark.parametrize("word", REFUSAL_WORDS)
def test_cs1014_a_path_shaped_pid_reaches_neither_detail_nor_the_written_row(
    word: str, tmp_path: Path
) -> None:
    """THE ARM: the same plant, the real guard, and the needle is nowhere.

    `_holder_pid` is the only thing standing between a lock file's `pid` field
    and the durable row, and the control above proves that without it the value
    lands. Graded on the BYTES `append_record` wrote, not on the dict it was
    handed, because the file is what outlives the session.
    """
    got = _cycle(_refusing(word, pid=PLANTED_PID))
    log = tmp_path / "cycles.jsonl"
    written = _write_and_read_back(got, log)

    # THE ANCHOR: the refusal really was read, so "no leak" is not the empty
    # truth of a driver that never looked at this payload.
    assert got["outcome"] == word
    # THE LEAK ASSERTIONS COME FIRST, so the `return pid` mutant reddens on the
    # property this arm is named for rather than on an anchor beside it.
    assert not _leaked(got["detail"], NEEDLE), f"a path-shaped pid reached detail on {word}"
    assert not _leaked(written, NEEDLE), f"a path-shaped pid reached the written row on {word}"
    assert not _leaked(json.dumps(got), NEEDLE), f"a path-shaped pid reached the record on {word}"
    assert "(pid None)" in got["detail"], f"the pid was not replaced by the guard: {word}"
    rows = [json.loads(line) for line in written.splitlines() if line.strip()]
    assert len(rows) == 1, "the writer did not write exactly one row"


@pytest.mark.parametrize("word", REFUSAL_WORDS)
def test_cs1014_an_honest_integer_pid_is_still_rendered(word: str, tmp_path: Path) -> None:
    """THE OTHER SIDE OF THE GUARD: a real pid is kept, so the fix is not erasure.

    A guard that returned None for everything would pass the arm above and
    destroy the one number an operator reads off a refusal row to find the
    holder. `bool` is an `int` subclass and is refused as a process.
    """
    got = _cycle(_refusing(word, pid=4242))
    written = _write_and_read_back(got, tmp_path / "cycles.jsonl")
    assert "(pid 4242)" in got["detail"], f"an honest pid was dropped on {word}"
    assert "(pid 4242)" in written, f"an honest pid did not reach the written row on {word}"

    flagged = _cycle(_refusing(word, pid=True))
    assert "(pid None)" in flagged["detail"], f"a bool was rendered as a pid on {word}"


# ===========================================================================
# CS-1015 - the refusal vocabulary, DERIVED from lanes.py rather than restated
# ===========================================================================

#: The emitter, read as SOURCE. Parsed rather than imported and introspected,
#: because the vocabulary is not a constant `lanes.py` exports - it lives in the
#: dict literals its refusal builders return - and exporting one would be a
#: second copy of the same words, which is the defect this item names.
LANES_SOURCE: Final = ROOT / "ops" / "loop" / "lanes.py"

#: The key a refusal is spelled under, the one literal this arm has to name.
REFUSED_KEY: Final = "refused"


def _is_refused_key(node: ast.AST | None) -> bool:
    """True when `node` is the literal `"refused"`."""
    return isinstance(node, ast.Constant) and node.value == REFUSED_KEY


def _emitted_refusals(source: str) -> tuple[set[str], list[int]]:
    """Every `refused` word `source` can emit, and every site it cannot read.

    THREE SPELLINGS of "put a word under `refused`", because the arm must not go
    green by a refactor that moves the word out of a dict literal: a dict
    literal key, a `dict(refused=...)` keyword, and a `x["refused"] = ...`
    subscript store. A value that is not a string literal cannot be derived, so
    it is returned as an OPAQUE site by line number rather than skipped - an
    unreadable site is a word this arm cannot vouch for, and it fails closed.

    Args:
        source: Python source text.

    Returns:
        The set of literal words, and the line numbers of opaque sites.
    """
    words: set[str] = set()
    opaque: list[int] = []

    def take(value: ast.AST, line: int) -> None:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            words.add(value.value)
        else:
            opaque.append(line)

    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values, strict=True):
                if _is_refused_key(key):
                    take(value, node.lineno)
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg == REFUSED_KEY:
                    take(keyword.value, node.lineno)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Subscript) and _is_refused_key(target.slice):
                    take(node.value, node.lineno)
    return words, opaque


def _driver_covers(words: set[str]) -> set[str]:
    """The emitted words the driver does NOT hold. Empty means covered."""
    return words - set(queue_loop._ACQUIRE_REFUSALS)  # noqa: SLF001 - the contract under test


def test_cs1015_every_refused_word_lanes_can_emit_is_one_the_driver_holds() -> None:
    """THE CONTRACT: `set(_ACQUIRE_REFUSALS)` covers what `lanes.py` emits.

    Measured when this item was filed: renaming the word at the emitter alone
    left every queue-loop arm passing, because each fake spelled the word again
    by hand. This arm reads the words OUT OF THE EMITTER, so a rename or a new
    word there is a word the driver does not hold, and this reddens.
    """
    words, opaque = _emitted_refusals(LANES_SOURCE.read_text(encoding="utf-8"))

    # ANTI-VACUITY: an empty derivation covers trivially. The emitter answers
    # at least the two faults CS-1011 separated, so fewer than two means the
    # parse is looking in the wrong place, not that the vocabulary shrank.
    assert len(words) >= len(REFUSAL_WORDS), f"the derivation found too few words: {sorted(words)}"
    assert opaque == [], f"lanes.py puts a non-literal under 'refused' at lines {opaque}"
    uncovered = sorted(_driver_covers(words))
    assert uncovered == [], f"lanes.py emits refusal words the driver does not hold: {uncovered}"


def test_cs1015_a_rename_in_a_temp_copy_of_lanes_reddens_the_contract(tmp_path: Path) -> None:
    """THE RENAME MUTANT, in a TEMP COPY, so the real emitter is never touched.

    Proves the arm above is live against the exact edit the item was filed on:
    one word renamed at the emitter and nowhere else.
    """
    pristine = LANES_SOURCE.read_text(encoding="utf-8")
    # THE BUILDER'S OWN LINE, anchored on its indentation: the same pair also
    # appears in `try_acquire_lane`'s docstring, and renaming prose would be a
    # mutant the AST never sees.
    old = '\n        "refused": "worktree_in_use",\n'
    sites = pristine.count(old)
    assert sites == 1, f"the rename site moved - re-aim the mutant ({sites} matches)"
    copy = tmp_path / "lanes.py"
    copy.write_text(
        pristine.replace(old, '\n        "refused": "worktree_taken",\n'), encoding="utf-8"
    )
    mutated = copy.read_text(encoding="utf-8")
    assert old not in mutated, "THE MUTANT DID NOT APPLY - a green here would measure nothing"

    words, opaque = _emitted_refusals(mutated)
    assert opaque == []
    assert _driver_covers(words) == {"worktree_taken"}, "the rename was not seen as uncovered"
    # AND THE PRISTINE FLOOR IN THE SAME RUN: the same derivation, the real file.
    assert _driver_covers(_emitted_refusals(pristine)[0]) == set()


def test_cs1015_a_new_word_or_an_opaque_value_in_a_temp_copy_reddens(tmp_path: Path) -> None:
    """GROWTH and INDIRECTION: a third word, and a word the parse cannot read.

    Both spellings a later edit could reach for - a new refusal builder, and a
    word held in a variable or a subscript store - must fail the contract
    rather than slip past it.
    """
    pristine = LANES_SOURCE.read_text(encoding="utf-8")
    grown = tmp_path / "lanes_grown.py"
    grown.write_text(
        pristine + '\n\ndef _third(state):\n    return {"ok": False, "refused": "lane_retired"}\n',
        encoding="utf-8",
    )
    words, _ = _emitted_refusals(grown.read_text(encoding="utf-8"))
    assert _driver_covers(words) == {"lane_retired"}, "a new emitter word was not seen"

    indirect = tmp_path / "lanes_indirect.py"
    indirect.write_text(
        pristine
        + "\n\nWORD = 'lane_held'\n\n"
        + "def _fourth(answer):\n"
        + "    answer['refused'] = 'lane_parked'\n"
        + "    return dict(ok=False, refused=WORD)\n",
        encoding="utf-8",
    )
    words, opaque = _emitted_refusals(indirect.read_text(encoding="utf-8"))
    assert "lane_parked" in _driver_covers(words), "a subscript-store word was not seen"
    assert len(opaque) == 1, f"a non-literal refusal word was not flagged opaque: {opaque}"


# ===========================================================================
# CS-1016 - a REAL worktree collision, driven into run_cycle and onto disk
# ===========================================================================


def test_cs1016_a_real_worktree_collision_is_written_as_one_naming_the_occupant(
    tmp_path: Path,
) -> None:
    """Two lanes, ONE worktree, REAL locks, and the row that reaches the file.

    Every CS-1011 arm fed `run_cycle` a hand-built refusal dict, so what the
    driver makes of the dict `lanes.try_acquire_lane` ACTUALLY returns was
    never measured, and CS-1011 exists because a row once said one thing while
    the driver decided another. Here `queue-b` takes a real lock on a tree,
    `queue` asks for the same tree through the real acquire, and the bytes
    `append_record` writes must name the fault and the occupying lane. Because
    the refusal word is whatever the emitter really answers, this is also
    CS-1015 end to end: a word renamed in `lanes.py` alone lands here as
    `lane_held` and reddens the outcome assertion.

    RESOURCE LIFETIME: both locks live under `tmp_path`, the occupant's is
    released in a `finally`, and the arm proves no lock file and no ownership
    entry survives it - a leaked entry in `lanes._OWNED` would outlive the test
    in this process and bias every later arm that reads it.
    """
    root = tmp_path / "locks"
    root.mkdir()
    shared = tmp_path / "cs-lane-shared"
    shared.mkdir()
    occupant = "queue-b"
    asking = "queue"
    assert occupant in lanes.LANES
    assert asking in lanes.LANES

    held = lanes.try_acquire_lane(occupant, run_id="cs1016a", worktree=shared, root=root)
    token = held.get("token")
    try:
        assert held.get("ok") is True, "the occupant could not take its real lock"
        assert lanes.lane_state(root, None, occupant)["state"] == lanes.RUNNING

        def acquire(lane: str, **kw: Any) -> dict[str, Any]:
            return lanes.try_acquire_lane(lane, root=root, **kw)

        def release(tok: Any, **_kw: Any) -> bool:
            return lanes.release_lane(tok, root=root)

        got = _cycle(acquire, worktree=str(shared), lane=asking, release=release)
        written = _write_and_read_back(got, tmp_path / "cycles.jsonl")
    finally:
        lanes.release_lane(token, root=root)

    rows = [json.loads(line) for line in written.splitlines() if line.strip()]
    assert len(rows) == 1, "the writer did not write exactly one row"
    row = rows[0]
    # THE FAULT, as the driver's own word, read off the FILE.
    assert row["outcome"] == queue_loop.OUTCOME_WORKTREE_IN_USE, (
        f"a real collision was written as {row['outcome']!r}"
    )
    assert row["worker_ok"] is False
    # THE OCCUPYING LANE, named - and not the asking lane, which holds nothing.
    assert f"lane {occupant!r}" in row["detail"], "the written row does not name the occupant"
    assert f"lane {asking!r}" not in row["detail"], "the row names the asking lane as occupant"
    # The tree's path is on the real refusal and must not ride into the file.
    assert not _leaked(written, shared.name), "the real refusal's worktree path reached the row"

    # NOTHING LEAKS: the asking lane never got a lock, the occupant's is gone,
    # and neither lock left an ownership entry behind in this process.
    leftover = sorted(p.name for p in root.iterdir())
    assert leftover == [], f"a lock survived the arm: {leftover}"
    assert lanes.lane_state(root, None, occupant)["state"] == lanes.FREE
    assert lanes.path_key(token) not in lanes._OWNED  # noqa: SLF001 - the lifetime under test
