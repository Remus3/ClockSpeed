"""CS-1226 - the one-shot inbox responder spawns a routed worker only when it should.

Every arm drives `ops/loop/inbox_responder.run_once` with every outward seam
injected: the channel surface, the lock, the route and the spawn. NO ARM
STARTS A PROCESS, takes the real mutex, reads the live channel, reads the real
user store or connects to the real proxy. The spawn is a spy that records what
it was handed and answers a canned exit.

NO ARM RENDERS AN ENV VALUE OR A PATH (CLAUDE.md rules 12 and 13). The log-line
arm grades the line STRUCTURALLY and binds each finding to a bool.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.loop import headless_route, inbox_responder, winmutex  # noqa: E402

#: A marker planted in the routed env and in the worker's output. It must never
#: reach the log line.
ENV_MARKER: Final = "plantedenvmarker"
BODY_MARKER: Final = "plantedbodymarker"
T0: Final = 1_000_000.0

USAGE_LIMIT_OUTPUT: Final = (
    '{"type":"result","is_error":true,"api_error_status":429,"num_turns":1,'
    f'"total_cost_usd":0,"result":"{BODY_MARKER}"}}'
)
OK_OUTPUT: Final = f'{{"type":"result","is_error":false,"result":"{BODY_MARKER}"}}'


class SpawnSpy:
    """Records every spawn and answers a canned (returncode, output)."""

    def __init__(self, returncode: int = 0, output: str = OK_OUTPUT) -> None:
        """Answer ``returncode`` and ``output`` on every call."""
        self.calls: list[dict[str, Any]] = []
        self.returncode = returncode
        self.output = output

    def __call__(
        self, argv: list[str], stdin: bytes, cwd: Path, env: dict[str, str], timeout: float
    ) -> tuple[int, str]:
        """Record the spawn and answer the canned exit."""
        self.calls.append(
            {"argv": list(argv), "stdin": stdin, "cwd": cwd, "env": env, "timeout": timeout}
        )
        return self.returncode, self.output


@contextmanager
def _free_lock() -> Iterator[None]:
    yield None


def _held_lock() -> Any:
    """A lock factory whose acquisition fails the way a held mutex does."""
    msg = "held by another run"
    raise winmutex.MutexTimeout(msg)


def _routed(base: Any) -> dict[str, str]:
    del base
    return {"ANTHROPIC_BASE_URL": f"http://127.0.0.1:1/{ENV_MARKER}"}


def _refusing(base: Any) -> dict[str, str]:
    del base
    raise headless_route.HeadlessRouteRefused(headless_route.REASON_UNSET)


def _surface(unread: int | str) -> Callable[[Any], dict[str, Any]]:
    def surface(root: Any) -> dict[str, Any]:
        del root
        return {"unread": unread, "names": [], "more": 0, "reason": ""}

    return surface


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A synthetic main tree: the worker prompt, a control dir, no data yet."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "headless-inbox.md").write_bytes(b"# synthetic worker prompt\n")
    (tmp_path / "control" / "lanes").mkdir(parents=True)
    return tmp_path


def _run(tree: Path, spy: SpawnSpy, **overrides: Any) -> int:
    kwargs: dict[str, Any] = {
        "root": tree,
        "control_dir": tree / "control",
        "now": lambda: T0,
        "surface": _surface(2),
        "lock": _free_lock,
        "route": _routed,
        "spawn": spy,
        "resolve": lambda _name: "synthetic-claude",
    }
    kwargs.update(overrides)
    return inbox_responder.run_once(**kwargs)


def _log_records(tree: Path) -> list[dict[str, Any]]:
    log = tree / inbox_responder.LOG_RELPATH
    if not log.is_file():
        return []
    return [json.loads(line) for line in log.read_bytes().decode("ascii").splitlines() if line]


def test_no_unread_exits_quietly_without_spawning(tree: Path) -> None:
    spy = SpawnSpy()
    code = _run(tree, spy, surface=_surface(0))
    assert (code, len(spy.calls), len(_log_records(tree))) == (0, 0, 0)


def test_an_unmeasured_channel_never_spawns(tree: Path) -> None:
    spy = SpawnSpy()
    code = _run(tree, spy, surface=_surface("UNMEASURED"))
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert (code, len(spy.calls), outcomes) == (
        inbox_responder.EXIT_UNMEASURED,
        0,
        ["unmeasured"],
    )


@pytest.mark.parametrize("sentinel", inbox_responder.STOP_RELPATHS)
def test_a_stop_sentinel_exits_without_spawning(tree: Path, sentinel: str) -> None:
    (tree / "control" / sentinel).write_bytes(b"")
    spy = SpawnSpy()
    code = _run(tree, spy)
    assert (code, len(spy.calls)) == (0, 0)


def test_the_stop_sentinel_is_checked_before_the_lock(tree: Path) -> None:
    (tree / "control" / inbox_responder.STOP_RELPATHS[0]).write_bytes(b"")
    taken: list[int] = []

    @contextmanager
    def counting() -> Iterator[None]:
        taken.append(1)
        yield None

    _run(tree, SpawnSpy(), lock=counting)
    assert taken == []


def test_a_held_lock_exits_without_spawning(tree: Path) -> None:
    spy = SpawnSpy()
    code = _run(tree, spy, lock=_held_lock)
    assert (code, len(spy.calls)) == (0, 0)


def test_a_route_refusal_exits_non_zero_without_spawning(tree: Path) -> None:
    spy = SpawnSpy()
    code = _run(tree, spy, route=_refusing)
    records = _log_records(tree)
    outcomes = [r.get("outcome") for r in records]
    assert (code, len(spy.calls), outcomes) == (
        inbox_responder.EXIT_ROUTE_REFUSED,
        0,
        ["route_refused"],
    )
    assert code != 0


def test_a_missing_cli_exits_non_zero_without_spawning(tree: Path) -> None:
    spy = SpawnSpy()
    code = _run(tree, spy, resolve=lambda _name: None)
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert (code, len(spy.calls), outcomes) == (
        inbox_responder.EXIT_SPAWN_FAILED,
        0,
        ["spawn_failed"],
    )


def test_an_unread_item_spawns_one_routed_worker(tree: Path) -> None:
    spy = SpawnSpy()
    code = _run(tree, spy)
    assert (code, len(spy.calls)) == (0, 1)
    call = spy.calls[0]
    argv_ok = call["argv"] == [
        "synthetic-claude",
        "-p",
        "--output-format",
        "json",
        "--dangerously-skip-permissions",
    ]
    stdin_ok = call["stdin"] == b"# synthetic worker prompt\n"
    cwd_ok = Path(call["cwd"]) == tree
    routed = call["env"].get("ANTHROPIC_BASE_URL", "").endswith(ENV_MARKER)
    no_bg = call["env"].get("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS") == "1"
    assert (argv_ok, stdin_ok, cwd_ok, routed, no_bg) == (True,) * 5
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert outcomes == ["ok"]


def test_a_failed_worker_exits_non_zero(tree: Path) -> None:
    spy = SpawnSpy(returncode=1, output="crash")
    code = _run(tree, spy)
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert (code, outcomes) == (inbox_responder.EXIT_WORKER_FAILED, ["failed"])


def test_a_usage_limit_writes_a_backoff_the_next_run_honours(tree: Path) -> None:
    limited = SpawnSpy(returncode=1, output=USAGE_LIMIT_OUTPUT)
    first = _run(tree, limited)
    backoff = tree / inbox_responder.BACKOFF_RELPATH
    written = backoff.is_file()
    assert (first, len(limited.calls), written) == (inbox_responder.EXIT_USAGE_LIMIT, 1, True)

    inside = SpawnSpy()
    second = _run(tree, inside, now=lambda: T0 + 60.0)
    assert (second, len(inside.calls)) == (0, 0)

    after = SpawnSpy()
    third = _run(tree, after, now=lambda: T0 + inbox_responder.BACKOFF_S + 1.0)
    assert (third, len(after.calls)) == (0, 1)
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert outcomes == ["usage_limit", "backoff", "ok"]


def test_a_garbled_backoff_file_does_not_block_forever(tree: Path) -> None:
    backoff = tree / inbox_responder.BACKOFF_RELPATH
    backoff.parent.mkdir(parents=True)
    backoff.write_bytes(b"{not json")
    spy = SpawnSpy()
    _run(tree, spy)
    assert len(spy.calls) == 1


def test_a_timed_out_worker_is_recorded(tree: Path) -> None:
    def timing_out(*_a: Any, **_k: Any) -> tuple[int, str]:
        raise inbox_responder.WorkerTimeoutError

    code = _run(tree, SpawnSpy(), spawn=timing_out)
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert (code, outcomes) == (inbox_responder.EXIT_TIMEOUT, ["timeout"])


def test_the_log_line_carries_no_path_env_value_or_body(tree: Path) -> None:
    """STRUCTURAL: a closed key set, scalar values, no separator, no planted marker."""
    _run(tree, SpawnSpy())
    _run(tree, SpawnSpy(returncode=1, output=USAGE_LIMIT_OUTPUT), now=lambda: T0 + 1)
    _run(tree, SpawnSpy(), route=_refusing, now=lambda: T0 + 99_999)
    records = _log_records(tree)
    raw = (tree / inbox_responder.LOG_RELPATH).read_bytes().decode("ascii")
    population = len(records)
    keys_closed = all(set(r) <= inbox_responder.LOG_KEYS for r in records)
    scalars = all(
        v is None or type(v) in (str, int, float, bool) for r in records for v in r.values()
    )
    strings = [v for r in records for v in r.values() if isinstance(v, str)]
    no_separator = not any(("/" in s) or ("\\" in s) for s in strings)
    no_tree = str(tree) not in raw and tree.name not in raw
    no_env = ENV_MARKER not in raw
    no_body = BODY_MARKER not in raw
    assert (population, keys_closed, scalars, no_separator, no_tree, no_env, no_body) == (
        3,
        True,
        True,
        True,
        True,
        True,
        True,
    )


def test_main_requires_once() -> None:
    with pytest.raises(SystemExit) as caught:
        inbox_responder.main([])
    assert caught.value.code == 2  # noqa: PLR2004 - argparse usage exit


def test_the_worker_prompt_carries_the_ack_and_provenance_fences() -> None:
    """The two adversary findings, pinned as text the worker cannot miss."""
    text = (ROOT / inbox_responder.PROMPT_RELPATH).read_bytes().decode("ascii")
    relists = "Re-list immediately before acking" in text
    mid_pass = "arrived mid-pass must never be" in text
    one_read = "ONE permitted read outside this tree" in text
    assert (relists, mid_pass, one_read) == (True, True, True)


def test_the_worker_prompt_is_tracked_beside_the_queue_prompt() -> None:
    prompt = ROOT / inbox_responder.PROMPT_RELPATH
    data = prompt.read_bytes()
    ascii_only = all(byte < 0x80 for byte in data)  # noqa: PLR2004 - 7-bit bound
    lf_only = b"\r" not in data
    assert (prompt.is_file(), ascii_only, lf_only) == (True, True, True)
