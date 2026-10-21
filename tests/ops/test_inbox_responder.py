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

import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile
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

from ops.fleet_kit import fleet_checklist  # noqa: E402
from ops.fleet_kit import fleet_headless as kit  # noqa: E402
from ops.fleet_kit import fleet_inbox as inbox_kit  # noqa: E402
from ops.loop import inbox_responder, inbox_status, inbox_surface, winmutex  # noqa: E402

TOOLS_DIR: Final = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import inbox_watch  # noqa: E402

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

#: Channel-note names in the channel's own shape. LW and EW are live sibling
#: codes; LL is the sibling MAIN 0230 retired; none is a world name.
LIVE_NOTE: Final = "2026-10-03-0708-from-LW-question-x.md"
ACK_NOTE: Final = "2026-10-03-0708-from-LW-INFORMATION-ACK-x.md"
ORDER_NOTE: Final = "2026-10-03-0915-from-MAIN-ORDER-x.md"
OWN_NOTE: Final = "2026-10-03-0935-from-CS-x.md"
RETIRED_NOTE: Final = "2026-10-05-0100-from-LL-question-x.md"
RETIRED_FIX: Final = "2026-10-05-0100-from-LL-FIX-x.md"

#: CS-1272 H2: the name shapes the kit's `note_sender` attributes to a sender
#: although they are not the canonical ``<stamp>-from-<CODE>-`` shape - a date
#: with no time, the sender leading the name, and an upper-cased ``FROM``. All
#: three were measured among the live LL notes, and the last one started a run.
#: The leading shape is assembled from ``SHAPE_STAMP`` so this source never
#: spells a sibling code glued to a dated name (tests/test_unregistered_lift.py).
SHAPE_STAMP: Final = "2026-09-07-2035"
RETIRED_DATE_ONLY: Final = "2026-09-12-from-LL-x.md"
RETIRED_LEADING: Final = f"from-LL-{SHAPE_STAMP}-x.md"
RETIRED_UPPER_FROM: Final = "2026-10-05-0230-FROM-LL-ORDER-x.md"
OWN_DATE_ONLY: Final = "2026-09-12-from-CS-x.md"
OWN_LEADING: Final = f"from-CS-{SHAPE_STAMP}-x.md"
OWN_UPPER_FROM: Final = "2026-10-05-0230-FROM-CS-ANSWER-x.md"


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
def tree() -> Iterator[Path]:
    """A synthetic main tree: the worker prompt, a control dir, no data yet - at a SHORT path.

    CS-1279: pytest's tmp_path nests the account name twice plus the test name,
    which leaves too little of MAX_PATH for the long-named notes the CS-1272 H3
    arms plant on a machine with long-path support off - the Windows default. A
    bare temp directory leaves the headroom the MAX_PATH arm grades, as the
    tests/test_inbox_watch.py `repo` fixture does for CS-1187.
    """
    root = Path(tempfile.mkdtemp(prefix="ir"))
    try:
        (root / "tools").mkdir()
        (root / "tools" / "headless-inbox.md").write_bytes(b"# synthetic worker prompt\n")
        (_control(root) / "lanes").mkdir(parents=True)
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


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
    _run(tree, RunSpy(), surface=_named(LIVE_NOTE))
    picked = [
        (
            k.get("floors_in_hooks"),
            k.get("bare"),
            k.get("stdin"),
            k.get("note", ""),
            k.get("kind"),
        )
        for k in seen
    ]
    assert picked == [(True, False, True, LIVE_NOTE, "inbox")]


def test_the_kit_refuses_bare_when_floors_live_in_hooks() -> None:
    """The door the responder relies on, read back from the vendored kit itself."""
    with pytest.raises(kit.Refused):
        kit.check_door(bare=True, floors_in_hooks=True)


def test_the_triage_spawn_takes_the_kits_triage_kwargs_whole_and_never_bare(
    tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS-1287, FLEET-KIT v11 ORDER item 3: every triage spawn splats the kit's own keywords.

    The keywords the kit names for a triage run on a floors-in-hooks tree reach
    ``kit.spawn`` unchanged - model, effort, the kit's own timeout, ``bare`` and
    ``floors_in_hooks`` - so no local override sits beside them, and the run
    the CLI is handed is never ``--bare``.
    """
    seen: list[dict[str, Any]] = []
    real = kit.spawn

    def recording(*args: Any, **kwargs: Any) -> Any:
        seen.append(dict(kwargs))
        return real(*args, **kwargs)

    monkeypatch.setattr(kit, "spawn", recording)
    spy = RunSpy()
    _run(tree, spy, surface=_named(ACK_NOTE))
    want = inbox_kit.triage_spawn_kwargs(True)
    picked = [{key: k.get(key) for key in want} for k in seen]
    kinds = [k.get("kind") for k in seen]
    bare_argv = ["--bare" in call["argv"] for call in spy.calls]
    timeouts = [call["timeout"] for call in spy.calls]
    assert (picked, kinds, bare_argv, timeouts, want["bare"]) == (
        [want],
        ["triage"],
        [False],
        [want["timeout"]],
        False,
    )


@pytest.mark.parametrize(
    ("names", "more", "model", "effort"),
    [
        (("2026-10-03-0708-from-LW-INFORMATION-ACK-x.md",), 0, "sonnet", "low"),
        (("2026-10-03-0708-from-LW-question-x.md",), 0, "sonnet", "medium"),
        (("2026-10-03-0915-from-MAIN-ORDER-x.md",), 0, "opus", "medium"),
        (
            ("2026-10-03-0915-from-EW-FIX-x.md", "2026-10-03-0708-from-LW-ACK-x.md"),
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


class _Unstartable(RunSpy):
    """A runner whose child never starts - the executable vanished under the kit."""

    def __call__(self, argv: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        """Fail the way a missing executable fails at process creation."""
        del argv, kw
        raise FileNotFoundError


def _refusing_pass(tree: Path, path: str) -> int:
    """Drive one pass down the named refused-start path. Nothing runs on any of them."""
    spy = _Unstartable() if path == "unstartable" else RunSpy()
    if path == "unmeasured":
        return _run(tree, spy, surface=_surface("UNMEASURED"))
    if path == "prompt-unreadable":
        (tree / inbox_responder.PROMPT_RELPATH).unlink()
        return _run(tree, spy)
    if path == "proxy-refused":
        return _run(tree, spy, seams=_seams(spy, url_source=lambda: None))
    if path == "budget-unreadable":
        _budget_file(tree).write_bytes(b"{garbled")
        return _run(tree, spy)
    return _run(tree, spy)


@pytest.mark.parametrize(
    ("path", "outcome"),
    [
        ("unmeasured", "unmeasured"),
        ("prompt-unreadable", "spawn_failed"),
        ("proxy-refused", "kit_refused"),
        ("budget-unreadable", "budget_refused"),
        ("unstartable", "spawn_failed"),
    ],
)
def test_a_refused_start_reads_the_kits_refused_task_never_halted(
    tree: Path, path: str, outcome: str
) -> None:
    """CS-1282 - FLEET-KIT v10's rule: a refused start reads task Idle, state refused.

    Only a halt reads Halted. The kit writes the same status file on its own
    refusal, so a board that published Halted here contradicted the kit's own
    write a moment earlier. The task is read from the kit, never respelled.
    """
    _refusing_pass(tree, path)
    status = _status(tree)
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    pair = (status.get("state"), status.get("task"))
    assert (pair, outcomes) == (("refused", kit.REFUSED_TASK), [outcome])


def test_the_kits_refused_task_is_a_basic_task_and_refused_is_not_one() -> None:
    """CS-1282 - v10 names a refused start's task Idle; no task is named Refused."""
    vocabulary = (
        kit.REFUSED_TASK,
        "Refused" in kit.TASKS,
        kit.REFUSED_TASK in inbox_status.TASKS,
        set(kit.TASKS) == set(inbox_status.TASKS),
    )
    assert vocabulary == ("Idle", False, True, True)


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
    """The responder matches the kit's refusal by its words; this reads them from the kit.

    CS-1282: from FLEET-KIT v10 the budget lock is an OS byte-range lock on a
    file that is never unlinked, so a lock FILE alone no longer holds it. The
    lock is held for real by one budget while a second asks.
    """
    path = tmp_path / "budget.json"
    holder = kit.RunBudget(path)
    with holder._lock(), pytest.raises(kit.Refused) as caught:  # noqa: SLF001 - hold it
        kit.RunBudget(path, lock_wait=0.1).start()
    matched = inbox_responder.is_lock_busy(caught.value)
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


# --- CS-1272 H: the spawn's label and kind, and the retired sibling -------------


def _usage_lines(tree: Path) -> list[dict[str, Any]]:
    """The kit's own usage log under the synthetic tree, one dict per line."""
    path = tree / kit.USAGE_REL
    if not path.is_file():
        return []
    text = path.read_bytes().decode("ascii")
    return [json.loads(line) for line in text.splitlines() if line]


def _stamped(line: dict[str, Any]) -> bool:
    """Whether the line carries an ISO timestamp the kit wrote."""
    ts = line.get("ts")
    if not isinstance(ts, str):
        return False
    try:
        datetime.fromisoformat(ts)
    except ValueError:
        return False
    return True


@pytest.mark.parametrize(
    ("names", "more", "label", "kind"),
    [
        ((LIVE_NOTE,), 0, LIVE_NOTE, "inbox"),
        ((ACK_NOTE,), 0, ACK_NOTE, "triage"),
        ((ORDER_NOTE, ACK_NOTE), 0, ORDER_NOTE, "order"),
        ((LIVE_NOTE, ORDER_NOTE), 0, LIVE_NOTE, "order"),
        ((OWN_NOTE, ACK_NOTE), 0, ACK_NOTE, "triage"),
        ((ACK_NOTE,), 1, ACK_NOTE, "inbox"),
    ],
    ids=[
        "question",
        "ack-only",
        "order-first",
        "order-second",
        "own-note-never-labels",
        "past-the-cap",
    ],
)
def test_the_usage_line_carries_ts_kind_and_label(
    tree: Path, names: tuple[str, ...], more: int, label: str, kind: str
) -> None:
    """FLEET-KIT v9: the kit's usage line names the note and the kind of the run.

    The CLI is the stub runner; nothing starts. The kind is "triage" exactly
    when the pass runs on the kit's triage shape (sonnet, effort low), and
    "inbox" for every other pass - except that a pass with ANY live ORDER, FIX
    or RULING is "order" (FLEET-KIT v18 KINDS). The kit itself maps "inbox" to
    "order" only from the LABEL, the first live note, so CS-1234 S5 passes
    "order" whenever such a note is live anywhere in the pass ("order-second").
    """
    _run(tree, RunSpy(), surface=_named(*names, more=more))
    lines = _usage_lines(tree)
    picked = [(line.get("note"), line.get("kind")) for line in lines]
    assert (picked, [_stamped(line) for line in lines]) == ([(label, kind)], [True])


def test_a_pass_with_no_listed_live_note_still_carries_a_label(tree: Path) -> None:
    """Every unread item past the listing cap: unnamed, so the label is authored, never empty."""
    _run(tree, RunSpy(), surface=_surface(2))
    lines = _usage_lines(tree)
    note = lines[0].get("note") if lines else None
    labelled = isinstance(note, str) and bool(note.strip())
    not_a_note = labelled and "-from-" not in str(note)
    kinds = [line.get("kind") for line in lines]
    assert (len(lines), labelled, not_a_note, kinds) == (1, True, True, ["inbox"])


@pytest.mark.parametrize(
    "names",
    [
        (RETIRED_NOTE,),
        (RETIRED_FIX,),
        ("2026-10-05-0100-from-ll-0-question-x.md",),
        (RETIRED_NOTE, OWN_NOTE),
        (RETIRED_DATE_ONLY,),
        (RETIRED_LEADING,),
        (RETIRED_UPPER_FROM,),
    ],
    ids=[
        "question",
        "fix",
        "lower-case-code",
        "beside-own-note",
        "date-only",
        "sender-leading",
        "upper-case-from",
    ],
)
def test_a_note_from_the_retired_sibling_never_spawns_and_is_skipped_by_name(
    tree: Path, names: tuple[str, ...]
) -> None:
    """MAIN 0230 item 4: never spawn a headless run for LL. The skip is recorded BY NAME."""
    spy = RunSpy()
    code = _run(tree, spy, surface=_named(*names))
    named = [(r.get("outcome"), r.get("reason")) for r in _log_records(tree)]
    assert (code, len(spy.calls), named, _status(tree).get("state")) == (
        0,
        0,
        [("retired_skip", "retired sibling LL")],
        "idle",
    )


@pytest.mark.parametrize(
    "name",
    [RETIRED_NOTE, RETIRED_FIX, RETIRED_DATE_ONLY, RETIRED_LEADING, RETIRED_UPPER_FROM],
    ids=["question", "fix", "date-only", "sender-leading", "upper-case-from"],
)
def test_every_name_the_kit_attributes_to_the_retired_sibling_is_retired(name: str) -> None:
    """CS-1272 H2: the responder decides the sender the SAME way the kit does.

    The kit's `note_sender` is the anti-vacuity half: each shape IS a note the
    kit says LL wrote, so a skip that misses it is a run the kit starts on LL.
    """
    decided = (
        kit.note_sender(name),
        inbox_responder.retired_sender(name),
        inbox_responder.is_damped(name),
    )
    assert decided == ("LL", "LL", True)


@pytest.mark.parametrize(
    "name",
    [OWN_NOTE, OWN_DATE_ONLY, OWN_LEADING, OWN_UPPER_FROM],
    ids=["canonical", "date-only", "sender-leading", "upper-case-from"],
)
def test_every_name_the_kit_calls_our_own_never_spawns(tree: Path, name: str) -> None:
    """CS-1272 H2 sibling: own-note detection shared the anchored sender read.

    The kit's `should_skip` answers "self" for each shape, so the responder
    damps each one as its own and starts nothing.
    """
    spy = RunSpy()
    code = _run(tree, spy, surface=_named(name))
    decided = (kit.should_skip(name, inbox_status.CODE), inbox_responder.is_damped(name))
    assert (decided, code, len(spy.calls)) == (("self", True), 0, 0)


@pytest.mark.parametrize(
    "name",
    ["2026-10-05-0230-from-LW-re-from-LL-x.md", "2026-10-05-0230-from-LW-re-from-CS-x.md"],
    ids=["retired-quoted", "own-quoted"],
)
def test_a_code_quoted_after_the_sender_is_not_the_sender(name: str) -> None:
    """The FIRST sender position decides, for the kit and the responder alike."""
    decided = (
        kit.note_sender(name),
        inbox_responder.retired_sender(name),
        inbox_responder.is_damped(name),
    )
    assert decided == ("LW", None, False)


@pytest.mark.parametrize(
    ("name", "damped"),
    [
        ("2026-10-03-0855-from-MAIN-CORRECTION-TERMINAL-x.md", False),
        ("2026-09-12-from-MAIN-CORRECTION-TERMINAL-x.md", True),
        (f"from-MAIN-{SHAPE_STAMP}-TERMINAL-x.md", True),
    ],
    ids=["canonical", "date-only", "sender-leading"],
)
def test_the_main_exemption_reads_the_canonical_shape_only(name: str, damped: bool) -> None:
    """CS-1272 H2 sibling, kept narrow on purpose: an exemption is a reason TO spawn.

    The kit attributes all three to MAIN and damps all three as terminal. The
    responder departs from the kit for MAIN's canonical names only; a damping
    reason reads the kit's wide attribution, an exemption from damping the
    narrow canonical one, so both directions fail closed.
    """
    decided = (kit.note_sender(name), kit.should_skip(name, inbox_status.CODE))
    assert (decided, inbox_responder.is_damped(name)) == (("MAIN", "terminal"), damped)


def test_a_retired_note_beside_live_mail_neither_labels_nor_weighs_the_run(tree: Path) -> None:
    """The live note starts the run; the retired FIX names it no label and buys it no model."""
    spy = RunSpy()
    code = _run(tree, spy, surface=_named(RETIRED_FIX, ACK_NOTE))
    argv = spy.calls[0]["argv"] if spy.calls else []
    picked = [(line.get("note"), line.get("kind")) for line in _usage_lines(tree)]
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert (
        code,
        len(spy.calls),
        _flag_value(argv, "--model"),
        _flag_value(argv, "--effort"),
        picked,
        outcomes,
    ) == (0, 1, "sonnet", "low", [(ACK_NOTE, "triage")], ["retired_skip", "ok"])


def prompt_fences(text: str) -> tuple[bool, bool, bool]:
    """The CS-1272 H fences in the worker prompt's text, each read to a bool."""
    retired = "retired sibling" in text and "LL" in text and "Delete nothing of it" in text
    kit_named = "ops/fleet_kit/fleet_headless.py" in text
    stale_route = "except through `ops/loop/headless_route.py`" in text
    return retired, kit_named, stale_route


def test_the_worker_prompt_carries_the_retired_sibling_and_kit_fences() -> None:
    """The worker skips the retired sibling by name, and names the kit as the one start path."""
    text = (ROOT / inbox_responder.PROMPT_RELPATH).read_bytes().decode("ascii")
    assert prompt_fences(text) == (True, True, False)


def test_the_retired_senders_mirror_the_outbound_senders_table() -> None:
    """The responder's mirror and the sender's table cannot part.

    MIRRORED, not imported: the A6 reach fence in
    tests/ops/test_lane_inbox_surface.py reddens on any lane module that
    reaches the sender, even by naming it. So this arm reads the sender's table
    as a literal from its source, and pins the mirror to its values.
    """
    import ast  # noqa: PLC0415 - this arm only

    source = (ROOT / "tools" / "outbound_send.py").read_bytes().decode("ascii")
    tables = [
        ast.literal_eval(node.value)
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "RETIRED_SIBLINGS"
        and node.value is not None
    ]
    codes = [frozenset(table.values()) for table in tables]
    assert codes == [inbox_responder.RETIRED_SENDERS]


# --- CS-1272 H: the item-13 checklist on the headless path ---------------------


def _progress_files(tree: Path) -> list[Path]:
    return sorted((tree / kit.PROGRESS_REL).glob("*.json"))


def _progress(tree: Path) -> dict[str, Any]:
    files = _progress_files(tree)
    if len(files) != 1:
        return {"files": len(files)}
    parsed: dict[str, Any] = json.loads(files[0].read_bytes().decode("ascii"))
    return parsed


def _row(row_id: str, task: str, state: str | None) -> dict[str, Any]:
    """One checklist row as the kit's own validator shapes it."""
    shaped: dict[str, Any] = fleet_checklist.item(row_id, task, state)
    return shaped


class _ProgressPeek(RunSpy):
    """The runner, reading the progress file at the moment the worker would start."""

    def __init__(self, tree: Path, returncode: int = 0, output: str = OK_OUTPUT) -> None:
        """Peek into ``tree``; answer like `RunSpy`."""
        super().__init__(returncode, output)
        self.tree = tree
        self.during: list[dict[str, Any]] = []

    def __call__(self, argv: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        """Record the progress file, then answer the canned exit."""
        self.during.append(_progress(self.tree))
        return super().__call__(argv, **kw)


def test_a_fire_writes_its_item_13_checklist_while_the_worker_runs(tree: Path) -> None:
    """FLEET items 12 and 13: the fire's progress file carries the remaining tasks."""
    peek = _ProgressPeek(tree)
    _run(tree, peek, surface=_named(OWN_NOTE, LIVE_NOTE, ORDER_NOTE, more=1))
    seen = peek.during[0] if peek.during else {}
    assert (len(peek.during), seen.get("status"), seen.get("checklist")) == (
        1,
        "running",
        [
            _row("N1", f"Handle {LIVE_NOTE}", "running"),
            _row("N2", f"Handle {ORDER_NOTE}", "running"),
            _row("MORE", "Handle 1 unread item past the listing cap", "running"),
        ],
    )


def test_a_finished_fire_leaves_no_remaining_task(tree: Path) -> None:
    _run(tree, RunSpy(), surface=_named(LIVE_NOTE))
    progress = _progress(tree)
    assert (progress.get("status"), progress.get("pct"), progress.get("checklist")) == (
        "done",
        100,
        [],
    )


def test_a_failed_fire_keeps_its_tasks_marked_failed(tree: Path) -> None:
    _run(tree, RunSpy(returncode=1, output="crash"), surface=_named(LIVE_NOTE))
    progress = _progress(tree)
    assert (progress.get("status"), progress.get("checklist")) == (
        "failed",
        [_row("N1", f"Handle {LIVE_NOTE}", "failed")],
    )


@pytest.mark.parametrize(
    ("names", "seams"),
    [
        ((), {}),
        ((RETIRED_NOTE,), {}),
        ((LIVE_NOTE,), {"url_source": lambda: None}),
    ],
    ids=["quiet", "retired-only", "kit-refused"],
)
def test_a_pass_that_starts_nothing_writes_no_checklist(
    tree: Path, names: tuple[str, ...], seams: dict[str, Any]
) -> None:
    spy = RunSpy()
    _run(tree, spy, surface=_named(*names), seams=_seams(spy, **seams))
    assert (len(spy.calls), _progress_files(tree)) == (0, [])


def test_a_note_name_at_the_display_cap_still_makes_a_one_line_task(tree: Path) -> None:
    """A display is capped at 120 chars, and so is the kit's task, so the row is cut to fit."""
    long_name = "2026-10-03-0708-from-LW-" + "x" * 93 + ".md"
    peek = _ProgressPeek(tree)
    _run(tree, peek, surface=_named(long_name))
    rows = peek.during[0].get("checklist", []) if peek.during else []
    tasks = [str(row.get("task")) for row in rows]
    fits = [len(task) <= fleet_checklist.TASK_MAX and task.startswith("Handle ") for task in tasks]
    assert (len(long_name), fits) == (120, [True])


def test_the_progress_file_carries_no_path_env_value_or_body(tree: Path) -> None:
    _run(tree, RunSpy(), surface=_named(LIVE_NOTE))
    _run(tree, RunSpy(returncode=1, output=BODY_MARKER), surface=_named(LIVE_NOTE))
    files = _progress_files(tree)
    raw = files[0].read_bytes().decode("ascii") if files else ""
    clean = (ENV_MARKER in raw, BODY_MARKER in raw, tree.name in raw, "\\" in raw, "/" in raw)
    assert (len(files), clean) == (1, (False, False, False, False, False))


# --- CS-1272 H3: every decision reads the REAL name, past both caps -------------

#: A topic long enough to push the sender past the watcher's display cap
#: (`inbox_watch.MAX_DISPLAY_CHARS`), so the DISPLAY loses what the kit reads.
#: CS-1279: and no longer. After the 16-character stamp the sender starts
#: wholly past the cap itself, not only past its cut, and every name below
#: keeps the MAX_PATH headroom the planted-path arm grades. The TERMINAL name
#: carries no class word, so its marker also sits past the cap at that length.
LONG_TOPIC: Final = "a" * 104
LONG_RETIRED: Final = f"2026-10-05-0230-{LONG_TOPIC}-from-LL-x.md"
LONG_OWN: Final = f"2026-10-05-0230-{LONG_TOPIC}-from-CS-x.md"
LONG_TERMINAL: Final = f"2026-10-05-0230-from-LW-{LONG_TOPIC}-TERMINAL.md"
LONG_ORDER: Final = f"2026-10-05-0230-{LONG_TOPIC}-from-MAIN-ORDER-x.md"

#: The kit reads its sender code upper-case only, so a lower-case code BEFORE
#: MAIN's is nobody's to the kit, and the note is MAIN's ORDER. Spelled with
#: ``from-ll-0-`` so this source carries no lower-case sibling marker
#: (tests/test_unregistered_lift.py).
LOWER_BEFORE_MAIN: Final = "2026-10-05-0230-x-from-ll-0-from-MAIN-ORDER-from-LL-z.md"

#: One more than the watcher lists by name, so exactly one item sits past the cap.
CAP_PLUS_ONE: Final = inbox_watch.MAX_LISTED + 1


def _channel(tree: Path, *names: str) -> None:
    """Plant ``names`` as unread notes in the tree's channel, the FIRST the newest."""
    inbox = tree / inbox_watch.INBOX_DIRNAME
    inbox.mkdir(exist_ok=True)
    for age, name in enumerate(names, start=1):
        note = inbox / name
        note.write_bytes(b"a synthetic note\n")
        stamp = T0 - 60.0 * age
        os.utime(note, (stamp, stamp))


def _stamped_names(shape: str, count: int) -> list[str]:
    """``count`` distinct canonical names in ``shape``, one stamp each."""
    return [shape.format(stamp=f"2026-10-05-02{minute:02d}") for minute in range(count)]


def _tree_bytes(tree: Path) -> bytes:
    """Every byte the pass wrote: the logs, the status, the progress and usage files."""
    written = [path for path in tree.rglob("*") if path.is_file()]
    channel = tree / inbox_watch.INBOX_DIRNAME
    return b"".join(path.read_bytes() for path in written if channel not in path.parents)


#: Windows MAX_PATH less its terminator: the longest path a default machine,
#: with long-path support off, can create. The tests/test_inbox_watch.py
#: precedent (CS-1187) grades its own planted notes against the same budget.
MAX_PATH_CHARS: Final = 259

#: Headroom over THIS machine's base for a longer account name or temp
#: directory elsewhere. A Windows account name runs to 20 characters.
MAX_PATH_HEADROOM: Final = 40

#: Every stamped shape an arm in this file plants through `_channel`.
PLANTED_SHAPES: Final = (
    "{stamp}-from-LL-ANSWER-x.md",
    "{stamp}-from-CS-ANSWER-x.md",
    "{stamp}-from-LW-ACK-TERMINAL-x.md",
    "{stamp}-from-LW-question-x.md",
)


def _planted_names() -> list[str]:
    """Every name an arm in this file plants in the channel through `_channel`."""
    stamped = [name for shape in PLANTED_SHAPES for name in _stamped_names(shape, CAP_PLUS_ONE)]
    named = [LONG_RETIRED, LONG_OWN, LONG_TERMINAL, LONG_ORDER, LOWER_BEFORE_MAIN, LIVE_NOTE]
    return [*named, *stamped]


def _longest_planted_path(tree: Path) -> int:
    """The character count of the longest full path `_channel` would create."""
    inbox = tree / inbox_watch.INBOX_DIRNAME
    return max(len(str(inbox / name)) for name in _planted_names())


def test_every_planted_note_fits_max_path_on_a_default_machine(tree: Path) -> None:
    """CS-1279: six arms died with FileNotFoundError on a clean-machine sandbox walk.

    The sandbox runs with long-path support at its Windows default (off), so a
    note whose full path exceeds MAX_PATH cannot be created at all. Graded by
    length rather than by creating the file, because a machine with long paths
    ON - the development box, CI - creates it happily and would never go red.
    """
    longest = _longest_planted_path(tree)
    budget = MAX_PATH_CHARS - MAX_PATH_HEADROOM
    assert longest <= budget, f"a planted path is {longest} chars, over {budget}"


@pytest.mark.parametrize(
    ("name", "sender"),
    [(LONG_RETIRED, "LL"), (LONG_OWN, "CS"), (LONG_TERMINAL, "LW")],
    ids=["retired", "own", "terminal"],
)
def test_a_damped_note_named_past_the_display_cap_never_spawns(
    tree: Path, name: str, sender: str
) -> None:
    """FIX 1: the decision reads the REAL name the kit reads, never the capped display.

    Anti-vacuity: the display the surface lists reads as LIVE, so a decision
    taken on it is a run the kit would start on a damped note.
    """
    _channel(tree, name)
    spy = RunSpy()
    code = _run(tree, spy, surface=None)
    shown = inbox_surface.surface(tree)["names"]
    display_reads_live = [inbox_responder.is_damped(str(n)) for n in shown] == [False]
    decided = (kit.note_sender(name), inbox_responder.is_damped(name), display_reads_live)
    assert (decided, code, len(spy.calls), _status(tree).get("state")) == (
        (sender, True, True),
        0,
        0,
        "idle",
    )


def test_a_retired_note_named_past_the_display_cap_is_skipped_by_name(tree: Path) -> None:
    """FIX 1: the named skip fires on the REAL name, and names the table's code only."""
    _channel(tree, LONG_RETIRED)
    _run(tree, RunSpy(), surface=None)
    named = [(r.get("outcome"), r.get("reason")) for r in _log_records(tree)]
    assert named == [("retired_skip", "retired sibling LL")]


def test_a_live_note_named_past_the_display_cap_is_weighed_by_its_real_name(tree: Path) -> None:
    """FIX 1 sibling: MAIN's ORDER past the display cap runs on the code model.

    The label stays the escaped display, and nothing past it - the part of the
    name only the decision read - reaches any file the pass wrote. CS-1234 S5:
    the kind is "order", decided on the real name too - the escaped label
    carries no class the kit could read, so the kit alone logged it "inbox".
    """
    _channel(tree, LONG_ORDER)
    spy = RunSpy()
    code = _run(tree, spy, surface=None)
    argv = spy.calls[0]["argv"] if spy.calls else []
    picked = [(line.get("note"), line.get("kind")) for line in _usage_lines(tree)]
    leaked = b"from-MAIN-ORDER" in _tree_bytes(tree)
    assert (code, len(spy.calls), _flag_value(argv, "--model"), picked, leaked) == (
        0,
        1,
        "opus",
        [(inbox_watch.safe_display(LONG_ORDER), "order")],
        False,
    )


@pytest.mark.parametrize(
    "shape",
    [
        "{stamp}-from-LL-ANSWER-x.md",
        "{stamp}-from-CS-ANSWER-x.md",
        "{stamp}-from-LW-ACK-TERMINAL-x.md",
    ],
    ids=["retired", "own", "terminal"],
)
def test_damped_notes_past_the_listing_cap_never_spawn(tree: Path, shape: str) -> None:
    """FIX 2: an item past the listing cap is judged on its real name, not counted live.

    Anti-vacuity: the surface really leaves exactly one item unnamed.
    """
    _channel(tree, *_stamped_names(shape, CAP_PLUS_ONE))
    spy = RunSpy()
    code = _run(tree, spy, surface=None)
    fact = inbox_surface.surface(tree)
    assert ((fact["unread"], fact["more"]), code, len(spy.calls), _status(tree).get("state")) == (
        (CAP_PLUS_ONE, 1),
        0,
        0,
        "idle",
    )


def test_a_live_note_past_the_listing_cap_still_runs_and_only_it_is_counted(tree: Path) -> None:
    """FIX 2 control: past the cap, the live note still starts a run, and alone fills MORE.

    Ten retired notes take every listed slot; one more retired note and one
    live note sit past the cap. The live one starts the run under the authored
    label, and the MORE row counts it alone.
    """
    _channel(tree, *_stamped_names("{stamp}-from-LL-ANSWER-x.md", CAP_PLUS_ONE), LIVE_NOTE)
    peek = _ProgressPeek(tree)
    code = _run(tree, peek, surface=None)
    seen = peek.during[0] if peek.during else {}
    picked = [(line.get("note"), line.get("kind")) for line in _usage_lines(tree)]
    assert (code, len(peek.calls), picked, seen.get("checklist")) == (
        0,
        1,
        [(inbox_responder.UNLISTED_LABEL, "inbox")],
        [_row("MORE", "Handle 1 unread item past the listing cap", "running")],
    )


def test_main_wins_where_a_lower_case_code_sits_before_its_sender(tree: Path) -> None:
    """FIX 3: the kit names MAIN, so the responder never skips the ORDER as retired."""
    _channel(tree, LOWER_BEFORE_MAIN)
    spy = RunSpy()
    code = _run(tree, spy, surface=None)
    decided = (
        kit.note_sender(LOWER_BEFORE_MAIN),
        inbox_responder.retired_sender(LOWER_BEFORE_MAIN),
        inbox_responder.is_damped(LOWER_BEFORE_MAIN),
    )
    outcomes = [r.get("outcome") for r in _log_records(tree)]
    assert (decided, code, len(spy.calls), outcomes) == (("MAIN", None, False), 0, 1, ["ok"])


def test_the_judged_fact_carries_verdicts_never_names_and_the_lane_fact_is_unchanged(
    tree: Path,
) -> None:
    """The surface hands the responder one closed-vocabulary word per item, never a name.

    The lane's own fact - the one its ledger row carries - keeps its four keys.
    """
    _channel(tree, LONG_RETIRED, *_stamped_names("{stamp}-from-LW-question-x.md", CAP_PLUS_ONE))
    lane = inbox_surface.surface(tree)
    judged = inbox_responder.judged_surface(tree)
    words = [*judged.get("verdicts", []), *judged.get("more_verdicts", [])]
    assert (
        sorted(lane),
        sorted(judged),
        len(words),
        set(words) <= inbox_responder.VERDICTS,
        LONG_TOPIC in json.dumps(judged["verdicts"] + judged["more_verdicts"]),
    ) == (
        ["more", "names", "reason", "unread"],
        ["more", "more_verdicts", "names", "reason", "unread", "verdicts"],
        CAP_PLUS_ONE + 1,
        True,
        False,
    )


# --- CS-1234 S5: the kit's refusal states and the declared stop sentinels ---------

#: This tree's own stop-sentinel declaration, read where the kit reads it (the
#: kit's `SENTINELS_REL` under the tree root), and the paths it declares.
DECLARATION: Final = ROOT / kit.SENTINELS_REL
DECLARED: Final = tuple(json.loads(DECLARATION.read_bytes().decode("ascii"))["paths"])

#: The responder's own floor, spelled as tree-relative paths.
OWN_DECLARED: Final = tuple(f"ops/loop/control/{rel}" for rel in inbox_responder.STOP_RELPATHS)


def _declare(tree: Path, payload: bytes | None = None) -> None:
    """This tree's REAL declaration (or ``payload``) at the synthetic tree's root."""
    target = tree / kit.SENTINELS_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(DECLARATION.read_bytes() if payload is None else payload)


def _plant(tree: Path, rel: str) -> None:
    planted = tree / rel
    planted.parent.mkdir(parents=True, exist_ok=True)
    planted.write_bytes(b"")


def _pair(tree: Path) -> tuple[Any, Any]:
    status = _status(tree)
    return status.get("state"), status.get("task")


class _CountingLock:
    """A lock factory that records every acquisition."""

    def __init__(self) -> None:
        """Nothing taken yet."""
        self.taken = 0

    @contextmanager
    def __call__(self) -> Iterator[None]:
        """Count the acquisition and hold nothing."""
        self.taken += 1
        yield None


def test_the_declaration_names_stops_beyond_the_responders_own() -> None:
    """Anti-vacuity: the declared-sentinel arms below plant paths the old list never read."""
    beyond = sorted(set(DECLARED) - set(OWN_DECLARED))
    covered = set(OWN_DECLARED) <= set(DECLARED)
    assert (beyond, covered) == (
        ["ops/loop/control/HOLD_MAIN_SPAWN", "ops/loop/control/lanes/QUEUE_STOP"],
        True,
    )


@pytest.mark.parametrize("rel", DECLARED)
def test_every_declared_stop_sentinel_halts_the_responder_quietly_before_the_lock(
    tree: Path, rel: str
) -> None:
    """CS-1234 S5 item 2: the responder halts on every path the declaration names.

    The kit's sentinels are tree-wide, so a standing QUEUE_STOP or
    HOLD_MAIN_SPAWN refuses every kit spawn into this tree - the responder's
    included. Ignoring them started nothing either; it took the lock, reached
    the kit, logged a route refusal and exited 3 on every tick. Read from the
    REAL declaration, so a path added there is covered here at once.
    """
    _declare(tree)
    _plant(tree, rel)
    lock = _CountingLock()
    spy = RunSpy()
    code = _run(tree, spy, lock=lock)
    assert (code, len(spy.calls), _pair(tree), _log_records(tree), lock.taken) == (
        0,
        0,
        ("halted", "Halted"),
        [],
        0,
    )


@pytest.mark.parametrize(
    "payload",
    [b"{garbled", b'{"paths": "x"}', b'{"paths": ["../outside"]}', b"\xff\xfe"],
    ids=["not-json", "paths-not-a-list", "path-outside-the-tree", "not-utf8"],
)
def test_an_unreadable_declaration_halts_the_responder_before_the_lock(
    tree: Path, payload: bytes
) -> None:
    """FAIL CLOSED, as the kit's own spawn does: an unreadable declaration halts."""
    _declare(tree, payload)
    lock = _CountingLock()
    spy = RunSpy()
    code = _run(tree, spy, lock=lock)
    assert (code, len(spy.calls), _pair(tree), _log_records(tree), lock.taken) == (
        0,
        0,
        ("halted", "Halted"),
        [],
        0,
    )


@pytest.mark.parametrize("sentinel", inbox_responder.STOP_RELPATHS)
def test_the_responders_own_stops_hold_beside_a_declaration_that_omits_them(
    tree: Path, sentinel: str
) -> None:
    """The decision pinned: the responder's own STOP and INBOX_STOP are a floor, not a default.

    The declaration ADDS to them; a declaration that drops one (or no
    declaration at all, the arms above) never lifts the responder's own stop.
    """
    _declare(tree, json.dumps({"paths": ["ops/loop/control/HOLD_MAIN_SPAWN"]}).encode("ascii"))
    (_control(tree) / sentinel).write_bytes(b"")
    spy = RunSpy()
    code = _run(tree, spy)
    assert (code, len(spy.calls), _pair(tree), _log_records(tree)) == (
        0,
        0,
        ("halted", "Halted"),
        [],
    )


def test_a_dangling_link_at_the_responders_own_stop_halts_as_the_kit_reads_it(
    tree: Path,
) -> None:
    """The kit halts on ANY entry at a declared path, a dangling link included; so does this."""
    link = _control(tree) / inbox_responder.STOP_RELPATHS[0]
    try:
        link.symlink_to(tree / "absent-target")
    except (OSError, NotImplementedError):
        pytest.skip("this machine cannot create a symbolic link")
    dangling = os.path.lexists(link) and not link.exists()
    spy = RunSpy()
    code = _run(tree, spy)
    assert (dangling, code, len(spy.calls), _pair(tree)) == (True, 0, 0, ("halted", "Halted"))


def _racing_surface(tree: Path) -> Callable[[Any], dict[str, Any]]:
    """A surface that plants a declared sentinel AFTER the responder's own check ran."""

    def surface(root: Any) -> dict[str, Any]:
        _plant(tree, "ops/loop/control/HOLD_MAIN_SPAWN")
        return _surface(2)(root)

    return surface


def _fallback_halted_route() -> Callable[[], dict[str, Any]]:
    """An armed fallback whose own route hit a limit too, so the kit refuses "fallback-halted".

    The state is the kit's own write, at the kit's own path - beside the
    per-test route file the suite guard names - so nothing outside the test's
    temporary directories is touched.
    """
    now = time.time()
    state = {
        "since": now - 60,
        "until": now + 3600,
        "from": "split",
        "to": "single",
        "halt_until": now + 3600,
    }
    kit._write_fallback_state(state)  # noqa: SLF001 - the kit's own state shape
    route = {"version": 1, "mode": "split", "fallback": {"mode": "single", "config_dir": "x"}}
    return lambda: dict(route)


def _unreachable(address: Any, timeout: float = 0.0) -> _Socket:
    del address, timeout
    raise ConnectionRefusedError


@pytest.mark.parametrize(
    ("path", "pair", "exit_code", "outcomes"),
    [
        ("halted", ("halted", "Halted"), 0, []),
        ("fallback-halted", ("limit", "Turn Limit Reached"), 0, ["limit"]),
        (
            "blocked",
            ("blocked", kit.REFUSED_TASK),
            inbox_responder.EXIT_ROUTE_REFUSED,
            ["kit_refused"],
        ),
        (
            "refused",
            ("refused", kit.REFUSED_TASK),
            inbox_responder.EXIT_ROUTE_REFUSED,
            ["kit_refused"],
        ),
        ("budget-spent", ("limit", "Turn Limit Reached"), 0, ["limit"]),
    ],
)
def test_a_kit_refusal_publishes_the_state_the_kits_own_write_used(
    tree: Path, path: str, pair: tuple[str, str], exit_code: int, outcomes: list[str]
) -> None:
    """CS-1234 S5 item 1: the board shows what the kit wrote for the refusal, never a second word.

    Every arm drives the REAL kit spawn down one refusal, and the ORACLE is the
    kit's own status write, read the instant the refusal leaves the kit. The
    responder then publishes over it; the two must agree, and the literal pair
    anchors both, so an oracle that read nothing cannot pass. "halted" plants a
    declared sentinel AFTER the responder's own check (a race the next tick
    catches quietly); "blocked" is an unreachable proxy (FLEET-KIT v14);
    "fallback-halted" is a limit on both routes (v20).
    """
    spy = RunSpy()
    seams = _seams(spy)
    surface = _surface(2)
    if path == "halted":
        _declare(tree)
        surface = _racing_surface(tree)
    elif path == "fallback-halted":
        seams = _seams(spy, route_source=_fallback_halted_route())
    elif path == "blocked":
        seams = _seams(spy, connect=_unreachable)
    elif path == "refused":
        seams = _seams(spy, url_source=lambda: None)
    else:
        _fill_budget(tree, [T0 - 3600 + i for i in range(kit.RUNS_CAP)])
    kit_wrote: list[tuple[Any, Any]] = []

    def recording(*args: Any, **kwargs: Any) -> tuple[dict[str, Any], str]:
        try:
            return inbox_responder.kit_spawn(*args, **kwargs)
        except kit.Refused:
            kit_wrote.append(_pair(tree))
            raise

    code = _run(tree, spy, seams=seams, surface=surface, spawn=recording)
    logged = [r.get("outcome") for r in _log_records(tree)]
    assert (kit_wrote, _pair(tree), code, len(spy.calls), logged) == (
        [pair],
        pair,
        exit_code,
        0,
        outcomes,
    )


def test_an_unreachable_proxy_still_exits_as_a_route_refusal_and_never_backs_off(
    tree: Path,
) -> None:
    """Blocked is a route refusal for the exit and the log: only the published state moved."""
    spy = RunSpy()
    _run(tree, spy, seams=_seams(spy, connect=_unreachable))
    second = _run(tree, spy, seams=_seams(spy, connect=_unreachable), now=lambda: T0 + 60)
    backoff = (tree / inbox_responder.BACKOFF_RELPATH).exists()
    assert (second, backoff, _pair(tree)) == (
        inbox_responder.EXIT_ROUTE_REFUSED,
        False,
        ("blocked", kit.REFUSED_TASK),
    )


# --- CS-1234 S5 repair: the state is the refusal's, never a re-read of the budget ---

#: Every refusal cause an arm can plant through the REAL kit spawn. The kit
#: raises ONE refusal - the first cause in its own check order - so with two
#: causes standing, the responder must publish the kit's write for THAT one.
#: The budget lock held busy is left out: the kit waits its full lock_wait (10
#: s) for it, and it is a budget-stage cause like "budget-unreadable", which
#: every pre-budget cause outranks the same way.
CAUSES: Final = (
    "halted",
    "fallback-halted",
    "refused",
    "blocked",
    "budget-full",
    "budget-unreadable",
)

#: The two causes that cannot stand together: both are the one budget file.
_EXCLUSIVE: Final = frozenset({"budget-full", "budget-unreadable"})

CAUSE_SETS: Final = [(cause,) for cause in CAUSES] + [
    pair for pair in itertools.combinations(CAUSES, 2) if set(pair) != _EXCLUSIVE
]

#: For each state the kit can write on a refusal, the exits and log outcomes
#: the responder may pair with it - "refused" covers a route refusal (exit 3)
#: and a counting failure (exit 9).
_CONSISTENT: Final[dict[str, set[tuple[int, tuple[str, ...]]]]] = {
    "halted": {(0, ())},
    "limit": {(0, ("limit",))},
    "blocked": {(inbox_responder.EXIT_ROUTE_REFUSED, ("kit_refused",))},
    "refused": {
        (inbox_responder.EXIT_ROUTE_REFUSED, ("kit_refused",)),
        (inbox_responder.EXIT_BUDGET_REFUSED, ("budget_refused",)),
    },
}


def _plant_causes(
    tree: Path, spy: RunSpy, causes: tuple[str, ...]
) -> tuple[dict[str, Any], Callable[[Any], dict[str, Any]]]:
    """Stand every cause in ``causes`` at once; returns the kit seams and the surface."""
    overrides: dict[str, Any] = {}
    surface = _surface(2)
    for cause in causes:
        if cause == "halted":
            _declare(tree)
            surface = _racing_surface(tree)
        elif cause == "fallback-halted":
            overrides["route_source"] = _fallback_halted_route()
        elif cause == "refused":
            overrides["url_source"] = lambda: None
        elif cause == "blocked":
            overrides["connect"] = _unreachable
        elif cause == "budget-full":
            _fill_budget(tree, [T0 - 3600 + i for i in range(kit.RUNS_CAP)])
        else:
            _budget_file(tree).write_bytes(b"{garbled")
    return _seams(spy, **overrides), surface


def _drive(tree: Path, causes: tuple[str, ...]) -> tuple[list[tuple[Any, Any]], int, int]:
    """One pass through the REAL kit spawn; the kit's own write is read as it refuses."""
    spy = RunSpy()
    seams, surface = _plant_causes(tree, spy, causes)
    kit_wrote: list[tuple[Any, Any]] = []

    def recording(*args: Any, **kwargs: Any) -> tuple[dict[str, Any], str]:
        try:
            return inbox_responder.kit_spawn(*args, **kwargs)
        except kit.Refused:
            kit_wrote.append(_pair(tree))
            raise

    code = _run(tree, spy, seams=seams, surface=surface, spawn=recording)
    return kit_wrote, code, len(spy.calls)


@pytest.mark.parametrize("budget", ["budget-full", "budget-unreadable"])
def test_an_unreachable_proxy_beside_a_spent_budget_still_reads_blocked(
    tree: Path, budget: str
) -> None:
    """The adversary's repro: the kit refuses on the proxy, before it counts the budget.

    It writes "blocked" / Idle. A responder that re-read the budget window
    published "limit", logged "limit" and exited 0, hiding the proxy fault.
    """
    kit_wrote, code, calls = _drive(tree, ("blocked", budget))
    logged = [r.get("outcome") for r in _log_records(tree)]
    assert (kit_wrote, _pair(tree), code, calls, logged) == (
        [("blocked", kit.REFUSED_TASK)],
        ("blocked", kit.REFUSED_TASK),
        inbox_responder.EXIT_ROUTE_REFUSED,
        0,
        ["kit_refused"],
    )


@pytest.mark.parametrize("causes", CAUSE_SETS, ids=["+".join(c) for c in CAUSE_SETS])
def test_every_pair_of_refusal_causes_publishes_the_kits_own_write(
    tree: Path, causes: tuple[str, ...]
) -> None:
    """Each cause alone and every pair together: the board reads what the kit wrote.

    The ORACLE is the kit's own status write, read the instant its refusal
    leaves the kit. Anti-vacuity: the kit wrote exactly once, in a state of
    the published vocabulary, and the exit and log outcome agree with it.
    """
    kit_wrote, code, calls = _drive(tree, causes)
    logged = tuple(r.get("outcome") for r in _log_records(tree))
    wrote = kit_wrote[0] if len(kit_wrote) == 1 else (None, None)
    consistent = (code, logged) in _CONSISTENT.get(str(wrote[0]), set())
    assert (len(kit_wrote), wrote[0] in inbox_status.STATES, _pair(tree) == wrote) == (
        1,
        True,
        True,
    )
    assert (calls, consistent) == (0, True)


def _aged(path: Path, epoch: float) -> None:
    os.utime(path, (epoch, epoch))


@pytest.mark.parametrize(
    "rel",
    [*OWN_DECLARED, "ops/loop/control/lanes/QUEUE_STOP", "ops/loop/control/HOLD_MAIN_SPAWN"],
)
def test_a_halt_is_shown_since_its_sentinel_was_placed(tree: Path, rel: str) -> None:
    """The halted status carries the standing sentinel's own mtime, never the tick's clock.

    Kills M11 (`_halted_since` ignoring every sentinel, so the halt reads as
    begun at every tick): the sentinel is aged an hour behind the pass clock.
    """
    _declare(tree)
    _plant(tree, rel)
    _aged(tree / rel, T0 - 3600)
    _run(tree, RunSpy())
    status = _status(tree)
    since = datetime.fromisoformat(status["task_started"]).timestamp()
    assert (_pair(tree), since) == (("halted", "Halted"), T0 - 3600)


def test_two_standing_sentinels_show_the_halt_since_the_earliest(tree: Path) -> None:
    """With an own stop and a declared one standing, the halt began at the older one."""
    _declare(tree)
    for rel, age in (("ops/loop/control/STOP", 600), ("ops/loop/control/HOLD_MAIN_SPAWN", 7200)):
        _plant(tree, rel)
        _aged(tree / rel, T0 - age)
    _run(tree, RunSpy())
    since = datetime.fromisoformat(_status(tree)["task_started"]).timestamp()
    assert since == T0 - 7200


def test_a_kit_halt_raced_past_the_own_check_shows_its_sentinels_age(tree: Path) -> None:
    """The kit-halted refusal path dates the halt from the sentinel too, not from the tick."""
    _declare(tree)
    rel = "ops/loop/control/HOLD_MAIN_SPAWN"

    def racing(root: Any) -> dict[str, Any]:
        _plant(tree, rel)
        _aged(tree / rel, T0 - 3600)
        return _surface(2)(root)

    spy = RunSpy()
    _run(tree, spy, surface=racing)
    since = datetime.fromisoformat(_status(tree)["task_started"]).timestamp()
    assert (_pair(tree), len(spy.calls), since) == (("halted", "Halted"), 0, T0 - 3600)
