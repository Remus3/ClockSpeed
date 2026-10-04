"""CS-1226 - the one-shot inbox responder spawns a routed worker only when it should.

CS-1231 SLICE C: the worker starts ONLY through the fleet kit's spawn helper.
Every arm drives `ops/loop/inbox_responder.run_once` through the REAL
`fleet_headless.spawn` with every outward seam of the kit injected: the proxy
URL source, the reachability probe, the executable lookup and the subprocess
runner. NO ARM STARTS A PROCESS, takes the real mutex, reads the live channel,
reads the real user store or connects to the real proxy. The runner is a spy
that records what the kit handed it and answers a canned exit.

The kit's budget and status files live under the synthetic tree's control
directory, which is where the responder's own status file lives too, exactly
as in the main tree.

NO ARM RENDERS AN ENV VALUE OR A PATH (CLAUDE.md rules 12 and 13). The log-line
arm grades the line STRUCTURALLY and binds each finding to a bool.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.fleet_kit import fleet_headless as kit  # noqa: E402
from ops.loop import inbox_responder, inbox_status, winmutex  # noqa: E402

#: A marker planted in the proxy URL and in the worker's output. It must never
#: reach the log line or the status file.
ENV_MARKER: Final = "plantedenvmarker"
BODY_MARKER: Final = "plantedbodymarker"
PROXY_URL: Final = f"http://127.0.0.1:3456/{ENV_MARKER}"

#: Near the real clock, because the kit stamps its budget with the real clock
#: and offers no seam for it - a synthetic epoch would age every kit start out
#: of, or into, the window the responder reads.
T0: Final = float(int(time.time()))

USAGE_LIMIT_OUTPUT: Final = (
    '{"type":"result","is_error":true,"api_error_status":429,"num_turns":1,'
    f'"total_cost_usd":0,"result":"{BODY_MARKER}"}}'
)
OK_OUTPUT: Final = f'{{"type":"result","is_error":false,"result":"{BODY_MARKER}"}}'


class RunSpy:
    """The kit's subprocess runner, recorded. Answers a canned (returncode, stdout)."""

    def __init__(self, returncode: int = 0, output: str = OK_OUTPUT) -> None:
        """Answer ``returncode`` and ``output`` on every call."""
        self.calls: list[dict[str, Any]] = []
        self.returncode = returncode
        self.output = output

    def __call__(self, argv: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        """Record the run and answer the canned exit."""
        self.calls.append({"argv": list(argv), **kw})
        return subprocess.CompletedProcess(argv, self.returncode, self.output, "")


class _Socket:
    def close(self) -> None:
        """Nothing to close."""


def _reachable(address: Any, timeout: float = 0.0) -> _Socket:
    del address, timeout
    return _Socket()


def _seams(spy: RunSpy, **overrides: Any) -> dict[str, Any]:
    seams: dict[str, Any] = {
        "url_source": lambda: PROXY_URL,
        "connect": _reachable,
        "exe_source": lambda: "synthetic-claude",
        "run": spy,
    }
    seams.update(overrides)
    return seams


@contextmanager
def _free_lock() -> Iterator[None]:
    yield None


def _held_lock() -> Any:
    """A lock factory whose acquisition fails the way a held mutex does."""
    msg = "held by another run"
    raise winmutex.MutexTimeout(msg)


def _surface(unread: int | str) -> Callable[[Any], dict[str, Any]]:
    def surface(root: Any) -> dict[str, Any]:
        del root
        return {"unread": unread, "names": [], "more": 0, "reason": ""}

    return surface


def _control(tree: Path) -> Path:
    return tree / "ops" / "loop" / "control"


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A synthetic main tree: the worker prompt, a control dir, no data yet."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "headless-inbox.md").write_bytes(b"# synthetic worker prompt\n")
    (_control(tmp_path) / "lanes").mkdir(parents=True)
    return tmp_path


def _run(tree: Path, spy: RunSpy, *, seams: dict[str, Any] | None = None, **overrides: Any) -> int:
    kwargs: dict[str, Any] = {
        "root": tree,
        "control_dir": _control(tree),
        "now": lambda: T0,
        "surface": _surface(2),
        "lock": _free_lock,
        "kit_seams": _seams(spy) if seams is None else seams,
        "next_tick": lambda _now: None,
    }
    kwargs.update(overrides)
    return inbox_responder.run_once(**kwargs)


def _log_records(tree: Path) -> list[dict[str, Any]]:
    log = tree / inbox_responder.LOG_RELPATH
    if not log.is_file():
        return []
    return [json.loads(line) for line in log.read_bytes().decode("ascii").splitlines() if line]


def _status(tree: Path) -> dict[str, Any]:
    path = _control(tree) / inbox_status.STATUS_NAME
    if not path.is_file():
        return {}
    parsed: dict[str, Any] = json.loads(path.read_bytes().decode("ascii"))
    return parsed


def _budget_file(tree: Path) -> Path:
    return tree / kit.BUDGET_REL


def _fill_budget(tree: Path, starts: list[float]) -> None:
    _budget_file(tree).write_bytes(json.dumps({"starts": starts}).encode("ascii"))


def _flag_value(argv: list[str], flag: str) -> str | None:
    return argv[argv.index(flag) + 1] if flag in argv else None


def test_no_unread_exits_quietly_without_spawning(tree: Path) -> None:
    spy = RunSpy()
    code = _run(tree, spy, surface=_surface(0))
    assert (code, len(spy.calls), len(_log_records(tree))) == (0, 0, 0)


def test_an_unmeasured_channel_never_spawns(tree: Path) -> None:
    spy = RunSpy()
    code = _run(tree, spy, surface=_surface("UNMEASURED"))
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert (code, len(spy.calls), outcomes) == (
        inbox_responder.EXIT_UNMEASURED,
        0,
        ["unmeasured"],
    )


@pytest.mark.parametrize("sentinel", inbox_responder.STOP_RELPATHS)
def test_a_stop_sentinel_exits_without_spawning(tree: Path, sentinel: str) -> None:
    (_control(tree) / sentinel).write_bytes(b"")
    spy = RunSpy()
    code = _run(tree, spy)
    assert (code, len(spy.calls)) == (0, 0)


def test_the_stop_sentinel_is_checked_before_the_lock(tree: Path) -> None:
    (_control(tree) / inbox_responder.STOP_RELPATHS[0]).write_bytes(b"")
    taken: list[int] = []

    @contextmanager
    def counting() -> Iterator[None]:
        taken.append(1)
        yield None

    _run(tree, RunSpy(), lock=counting)
    assert taken == []


def test_a_held_lock_exits_without_spawning(tree: Path) -> None:
    spy = RunSpy()
    code = _run(tree, spy, lock=_held_lock)
    assert (code, len(spy.calls)) == (0, 0)


@pytest.mark.parametrize(
    "refusing",
    [
        {"url_source": lambda: None},
        {"url_source": lambda: "http://example.com:3456"},
        {"url_source": lambda: "https://127.0.0.1:3456"},
    ],
    ids=["unset", "not-loopback", "not-plain-http"],
)
def test_a_proxy_refusal_exits_non_zero_without_spawning(
    tree: Path, refusing: dict[str, Any]
) -> None:
    spy = RunSpy()
    code = _run(tree, spy, seams=_seams(spy, **refusing))
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    state = _status(tree).get("state")
    counted = _budget_file(tree).exists()
    assert (code, len(spy.calls), outcomes, state, counted) == (
        inbox_responder.EXIT_ROUTE_REFUSED,
        0,
        ["kit_refused"],
        "refused",
        False,
    )


def test_an_unreachable_proxy_is_refused_without_spawning(tree: Path) -> None:
    def unreachable(address: Any, timeout: float = 0.0) -> _Socket:
        del address, timeout
        raise ConnectionRefusedError

    spy = RunSpy()
    code = _run(tree, spy, seams=_seams(spy, connect=unreachable))
    assert (code, len(spy.calls)) == (inbox_responder.EXIT_ROUTE_REFUSED, 0)


def test_a_missing_cli_is_refused_by_the_kit_without_spawning(tree: Path) -> None:
    def missing() -> str:
        msg = "claude not found on PATH (working directory excluded)"
        raise kit.Refused(msg)

    spy = RunSpy()
    code = _run(tree, spy, seams=_seams(spy, exe_source=missing))
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert (code, len(spy.calls), outcomes) == (
        inbox_responder.EXIT_ROUTE_REFUSED,
        0,
        ["kit_refused"],
    )


def test_an_unread_item_spawns_one_worker_through_the_kit(tree: Path) -> None:
    spy = RunSpy()
    code = _run(tree, spy)
    assert (code, len(spy.calls)) == (0, 1)
    call = spy.calls[0]
    argv = call["argv"]
    lean = (
        argv[:2] == ["synthetic-claude", "-p"]
        and "--strict-mcp-config" in argv
        and _flag_value(argv, "--setting-sources") == kit.DEFAULT_SOURCES
        and "--bare" not in argv
        and "--no-session-persistence" in argv
        and argv[-1] == "--dangerously-skip-permissions"
    )
    stdin_ok = call["input"] == "# synthetic worker prompt\n" and "# synthetic" not in argv
    cwd_ok = Path(call["cwd"]) == tree
    env = call["env"]
    routed = env.get("ANTHROPIC_BASE_URL") == PROXY_URL
    no_key = "ANTHROPIC_API_KEY" not in env
    no_bg = all(env.get(k) == v for k, v in inbox_responder.WORKER_ENV.items())
    no_window = call["creationflags"] == kit._NO_WINDOW  # noqa: SLF001 - the kit's own flag
    timeout_ok = call["timeout"] == inbox_responder.WORKER_TIMEOUT_S
    assert (lean, stdin_ok, cwd_ok, routed, no_key, no_bg, no_window, timeout_ok) == (True,) * 8
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert outcomes == ["ok"]


def test_the_worker_env_is_set_for_the_spawn_only(tree: Path) -> None:
    """The kit builds the child's env from this process's; nothing leaks past the spawn."""
    before = {key: os.environ.get(key) for key in inbox_responder.WORKER_ENV}
    _run(tree, RunSpy())
    after = {key: os.environ.get(key) for key in inbox_responder.WORKER_ENV}
    changed = sorted(key for key in before if before[key] != after[key])
    assert changed == []


def test_the_default_spawn_declares_floors_in_hooks_and_never_bare(
    tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS floors live in hooks, so the kit must be told - and --bare is never asked for."""
    seen: list[dict[str, Any]] = []
    real = kit.spawn

    def recording(*args: Any, **kwargs: Any) -> Any:
        seen.append(dict(kwargs))
        return real(*args, **kwargs)

    monkeypatch.setattr(kit, "spawn", recording)
    _run(tree, RunSpy())
    picked = [
        (k.get("floors_in_hooks"), k.get("bare"), k.get("stdin"), k.get("note", "")) for k in seen
    ]
    assert picked == [(True, False, True, "")]


def test_the_kit_refuses_bare_when_floors_live_in_hooks() -> None:
    """The door the responder relies on, read back from the vendored kit itself."""
    with pytest.raises(kit.Refused):
        kit.check_door(bare=True, floors_in_hooks=True)


@pytest.mark.parametrize(
    ("names", "more", "model", "effort"),
    [
        (("2026-10-03-0708-from-LW-INFORMATION-ACK-x.md",), 0, "sonnet", "low"),
        (("2026-10-03-0708-from-LW-question-x.md",), 0, "sonnet", "medium"),
        (("2026-10-03-0915-from-MAIN-ORDER-x.md",), 0, "opus", "medium"),
        (
            ("2026-10-03-0915-from-LL-FIX-x.md", "2026-10-03-0708-from-LW-ACK-x.md"),
            0,
            "opus",
            "medium",
        ),
        (("2026-10-03-0708-from-LW-ACK-x.md",), 1, "opus", "medium"),
    ],
    ids=["ack", "question", "order", "fix-beside-ack", "past-the-cap"],
)
def test_the_model_and_effort_follow_the_live_note_names(
    tree: Path, names: tuple[str, ...], more: int, model: str, effort: str
) -> None:
    spy = RunSpy()
    _run(tree, spy, surface=_named(*names, more=more))
    argv = spy.calls[0]["argv"]
    assert (_flag_value(argv, "--model"), _flag_value(argv, "--effort")) == (model, effort)


def test_a_failed_worker_exits_non_zero(tree: Path) -> None:
    spy = RunSpy(returncode=1, output="crash")
    code = _run(tree, spy)
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert (code, outcomes) == (inbox_responder.EXIT_WORKER_FAILED, ["failed"])


def test_a_usage_limit_writes_a_backoff_the_next_run_honours(tree: Path) -> None:
    limited = RunSpy(returncode=1, output=USAGE_LIMIT_OUTPUT)
    first = _run(tree, limited)
    backoff = tree / inbox_responder.BACKOFF_RELPATH
    written = backoff.is_file()
    assert (first, len(limited.calls), written) == (inbox_responder.EXIT_USAGE_LIMIT, 1, True)

    inside = RunSpy()
    second = _run(tree, inside, now=lambda: T0 + 60.0)
    assert (second, len(inside.calls)) == (0, 0)

    after = RunSpy()
    third = _run(tree, after, now=lambda: T0 + inbox_responder.BACKOFF_S + 1.0)
    assert (third, len(after.calls)) == (0, 1)
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert outcomes == ["usage_limit", "backoff", "ok"]


def test_a_garbled_backoff_file_does_not_block_forever(tree: Path) -> None:
    backoff = tree / inbox_responder.BACKOFF_RELPATH
    backoff.parent.mkdir(parents=True)
    backoff.write_bytes(b"{not json")
    spy = RunSpy()
    _run(tree, spy)
    assert len(spy.calls) == 1


def test_a_timed_out_worker_is_recorded(tree: Path) -> None:
    class TimingOut(RunSpy):
        def __call__(self, argv: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
            super().__call__(argv, **kw)
            raise subprocess.TimeoutExpired(argv, inbox_responder.WORKER_TIMEOUT_S)

    code = _run(tree, TimingOut())
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert (code, outcomes, _status(tree).get("state")) == (
        inbox_responder.EXIT_TIMEOUT,
        ["timeout"],
        "idle",
    )


def test_a_worker_that_cannot_start_is_recorded(tree: Path) -> None:
    class Unstartable(RunSpy):
        def __call__(self, argv: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
            del argv, kw
            raise FileNotFoundError

    code = _run(tree, Unstartable())
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert (code, outcomes, _status(tree).get("state")) == (
        inbox_responder.EXIT_SPAWN_FAILED,
        ["spawn_failed"],
        "refused",
    )


def test_the_log_line_carries_no_path_env_value_or_body(tree: Path) -> None:
    """STRUCTURAL: a closed key set, scalar values, no separator, no planted marker."""
    _run(tree, RunSpy())
    _run(tree, RunSpy(returncode=1, output=USAGE_LIMIT_OUTPUT), now=lambda: T0 + 1)
    refusing = RunSpy()
    _run(
        tree,
        refusing,
        seams=_seams(refusing, url_source=lambda: "http://example.com:1/" + ENV_MARKER),
        now=lambda: T0 + 99_999,
    )
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
    keyed = "--ack-keys" in text and "--keys" in text
    no_plain_ack = "NEVER run plain `--ack`" in text
    assert (relists, mid_pass, one_read, keyed, no_plain_ack) == (True,) * 5


def test_the_worker_prompt_is_tracked_beside_the_queue_prompt() -> None:
    prompt = ROOT / inbox_responder.PROMPT_RELPATH
    data = prompt.read_bytes()
    ascii_only = all(byte < 0x80 for byte in data)  # noqa: PLR2004 - 7-bit bound
    lf_only = b"\r" not in data
    assert (prompt.is_file(), ascii_only, lf_only) == (True, True, True)


def test_the_responder_reaches_no_process_api_but_the_kit() -> None:
    """FLEET item 10: the kit is the only path that starts `claude`. Read structurally."""
    import ast  # noqa: PLC0415 - this arm only

    source = (ROOT / "ops" / "loop" / "inbox_responder.py").read_bytes().decode("ascii")
    tree = ast.parse(source)
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    starts = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and node.attr in {"Popen", "run", "call", "system"}
        and isinstance(node.value, ast.Name)
        and node.value.id in {"subprocess", "os"}
    }
    assert (sorted(imported & {"subprocess", "shutil"}), sorted(starts)) == ([], [])


# --- CS-1234: the status file, the 120-per-24h cap, the loop damping -----------


def _named(*names: str, more: int = 0) -> Callable[[Any], dict[str, Any]]:
    def surface(root: Any) -> dict[str, Any]:
        del root
        return {"unread": len(names) + more, "names": list(names), "more": more, "reason": ""}

    return surface


@pytest.mark.parametrize("sentinel", inbox_responder.STOP_RELPATHS)
def test_the_halted_path_still_publishes_its_status(tree: Path, sentinel: str) -> None:
    (_control(tree) / sentinel).write_bytes(b"")
    spy = RunSpy()
    code = _run(tree, spy)
    status = _status(tree)
    pair = (status.get("state"), status.get("task"))
    sentinel_kept = (_control(tree) / sentinel).exists()
    no_counter = not _budget_file(tree).exists()
    assert (code, len(spy.calls), pair, sentinel_kept, no_counter, _log_records(tree)) == (
        0,
        0,
        ("halted", "Halted"),
        True,
        True,
        [],
    )


def test_a_quiet_channel_publishes_idle(tree: Path) -> None:
    _run(tree, RunSpy(), surface=_surface(0))
    status = _status(tree)
    assert (status.get("state"), status.get("task"), status.get("runs_in_window")) == (
        "idle",
        "Idle",
        0,
    )


def test_a_spawn_is_counted_by_the_kit_and_published_while_it_runs(tree: Path) -> None:
    """The kit counts the start; the status the run is SHOWN under is the responder's."""
    seen: list[tuple[Any, Any, Any, Any]] = []

    class Peeking(RunSpy):
        def __call__(self, argv: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
            during = _status(tree)
            seen.append(
                (
                    during.get("state"),
                    during.get("task"),
                    during.get("runs_in_window"),
                    "kit" in during,
                )
            )
            return super().__call__(argv, **kw)

    clock = iter([T0 + step for step in range(20)])
    code = _run(tree, Peeking(), now=lambda: next(clock, T0 + 40))
    after = _status(tree)
    budget = json.loads(_budget_file(tree).read_bytes().decode("ascii"))
    assert (code, seen, after.get("state"), after.get("runs_in_window"), len(budget["starts"])) == (
        0,
        [("running", "Running Session", 1, False)],
        "idle",
        1,
        1,
    )


def test_at_the_cap_nothing_starts_and_the_limit_is_published(tree: Path) -> None:
    starts = [T0 - 3600 + i for i in range(kit.RUNS_CAP)]
    _fill_budget(tree, starts)
    spy = RunSpy()
    code = _run(tree, spy)
    status = _status(tree)
    frees = datetime.fromisoformat(status["cap_frees_at"]).timestamp()
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    pair = (status.get("state"), status.get("task"), status.get("runs_in_window"))
    assert (code, len(spy.calls), pair, frees, outcomes) == (
        0,
        0,
        ("limit", "Turn Limit Reached", 120),
        T0 - 3600 + 86400,
        ["limit"],
    )


@pytest.mark.parametrize("garbage", [b"{garbled", b"", b'{"starts": "x"}', b"[]"])
def test_an_unreadable_budget_refuses_the_start_and_is_never_reset(
    tree: Path, garbage: bytes
) -> None:
    budget = _budget_file(tree)
    budget.write_bytes(garbage)
    spy = RunSpy()
    code = _run(tree, spy)
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert (
        code,
        len(spy.calls),
        _status(tree).get("state"),
        outcomes,
        budget.read_bytes(),
    ) == (inbox_responder.EXIT_BUDGET_REFUSED, 0, "refused", ["budget_refused"], garbage)


def test_a_busy_budget_lock_refuses_as_a_counting_failure(tree: Path) -> None:
    """The kit's lock-busy refusal is logged with the unreadable budget, never as a proxy fault."""

    def busy(*_args: Any, **_kwargs: Any) -> tuple[dict[str, Any], str]:
        raise kit.Refused(inbox_responder.KIT_LOCK_BUSY)

    spy = RunSpy()
    code = _run(tree, spy, spawn=busy)
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert (code, outcomes) == (inbox_responder.EXIT_BUDGET_REFUSED, ["budget_refused"])


def test_the_lock_busy_words_are_the_vendored_kits_own(tmp_path: Path) -> None:
    """The responder matches the kit's refusal by its words; this reads them from the kit."""
    path = tmp_path / "budget.json"
    path.with_name(path.name + ".lock").write_bytes(b"0")
    with pytest.raises(kit.Refused) as caught:
        kit.RunBudget(path, lock_wait=0.1).start()
    matched = str(caught.value) == inbox_responder.KIT_LOCK_BUSY
    assert matched is True


def test_a_backoff_is_published(tree: Path) -> None:
    _run(tree, RunSpy(returncode=1, output=USAGE_LIMIT_OUTPUT))
    first = _status(tree)
    _run(tree, RunSpy(), now=lambda: T0 + 60)
    second = _status(tree)
    assert ((first.get("state"), first.get("task")), second.get("state")) == (
        ("backoff", "Backing Off"),
        "backoff",
    )


def test_a_held_lock_refreshes_the_running_status(tree: Path) -> None:
    window = inbox_status.Window(count=1, frees_at=T0 + 86400)
    inbox_status.publish(
        _control(tree),
        now=T0,
        state="running",
        task="Running Session",
        task_started=T0,
        eta_s=None,
        next_tick=None,
        window=window,
    )
    _run(tree, RunSpy(), lock=_held_lock, now=lambda: T0 + 900)
    status = _status(tree)
    moved = datetime.fromisoformat(status["updated"]).timestamp() == T0 + 900
    assert (moved, status.get("task")) == (True, "Running Session")


@pytest.mark.parametrize(
    "names",
    [
        ("2026-10-03-0935-from-CS-ANSWER-to-MAIN.md",),
        ("2026-10-03-0708-from-LW-RESPONDER-ACK-TERMINAL-no-reply.md",),
        ("2026-10-03-0708-from-RSC-auto-reply-is-noreply.md",),
        ("2026-10-03-0708-from-LL-INFORMATION-done-No-Reply.md",),
        ("2026-10-03-0935-from-CS-x.md", "2026-10-03-0708-from-LW-terminal.md"),
    ],
)
def test_own_and_terminal_notes_never_spawn(tree: Path, names: tuple[str, ...]) -> None:
    spy = RunSpy()
    code = _run(tree, spy, surface=_named(*names))
    assert (code, len(spy.calls), _status(tree).get("state")) == (0, 0, "idle")


@pytest.mark.parametrize(
    ("names", "more"),
    [
        (("2026-10-03-0855-from-MAIN-CORRECTION-never-spawn-on-TERMINAL-no-reply.md",), 0),
        (("2026-10-03-0007-from-RSC-auto-reply-to-2026-10-03-0002-from-CS-ANSWER.md",), 0),
        (("2026-10-03-0935-from-CS-x.md", "2026-10-03-0000-from-SS-INFORMATION.md"), 0),
        (("2026-10-03-0935-from-CS-x.md",), 1),
    ],
)
def test_live_mail_beside_damped_mail_still_spawns(
    tree: Path, names: tuple[str, ...], more: int
) -> None:
    spy = RunSpy()
    code = _run(tree, spy, surface=_named(*names, more=more))
    assert (code, len(spy.calls)) == (0, 1)


def test_the_status_file_carries_no_path_or_env_value(tree: Path) -> None:
    _run(tree, RunSpy())
    raw = (_control(tree) / inbox_status.STATUS_NAME).read_bytes().decode("ascii")
    clean = (ENV_MARKER in raw, BODY_MARKER in raw, tree.name in raw, "\\" in raw, "/" in raw)
    assert clean == (False, False, False, False, False)
