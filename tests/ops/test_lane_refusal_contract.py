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
from ops.loop import queue_loop  # noqa: E402

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
