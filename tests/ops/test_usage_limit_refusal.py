"""CS-1178 - a usage-limit refusal is REFUSED, NOT RUN, and the driver backs off.

A headless run refused by a usage limit ends in about five seconds with exit 1,
one turn, zero cost, an error flag and an `api_error_status` of 429. Read by
exit code and duration alone it is a crashed executor; read by outcome word it
was, before this item, a cycle that ran - `completed`, with a row and a cycle
of the night's budget spent on it, and the next cycle launched into the same
refusal 45 seconds later.

EVERY FIXTURE HERE IS HAND-AUTHORED. No real run receipt, no real cost figure
and no real log enters the tree: the result dicts below are written from the
refusal's SHAPE, and the worker log is assembled under `tmp_path` in the layout
`ops/loop/run_lane.ps1` writes - a header line, the worker's output, an exit
line - with the worker's output being the JSON result object a run emits when
asked for JSON output, which the runner now asks for. The last arm runs the
REAL runner over a shim `claude` and feeds the driver the log it wrote.

No arm spawns a process, sleeps, takes a lock or reads the live channel.
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# A PLAIN IMPORT, never importorskip: a missing driver is a COLLECTION error.
from ops.loop import queue_loop  # noqa: E402

#: Planted in the result's free text, so an arm can prove the driver never
#: renders the worker's words into the durable row.
NEEDLE: Final = "cs1178-result-text-needle"

#: THE REFUSAL, by shape: exit 1 is on the log's exit line; here are one turn,
#: zero cost, the error flag and the 429.
REFUSAL: Final = {
    "type": "result",
    "is_error": True,
    "num_turns": 1,
    "total_cost_usd": 0,
    "api_error_status": 429,
    "result": f"synthetic usage limit refusal {NEEDLE}",
}

#: THE CONTROL: an ordinary run that did work and then FAILED. Exit 1 and the
#: error flag too - what separates it is that it ran.
ORDINARY_FAILURE: Final = {
    "type": "result",
    "is_error": True,
    "num_turns": 14,
    "total_cost_usd": 0.5,
    "result": "synthetic ordinary failure",
}

#: A 429 that arrived MID-RUN, after real turns and real cost. It is a run that
#: happened and was then throttled, not a refusal - work may be on disk.
MID_RUN_429: Final = {
    "type": "result",
    "is_error": True,
    "num_turns": 9,
    "total_cost_usd": 0.25,
    "api_error_status": 429,
    "result": "synthetic mid-run throttle",
}

#: A clean, ordinary run.
ORDINARY_SUCCESS: Final = {
    "type": "result",
    "is_error": False,
    "num_turns": 30,
    "total_cost_usd": 1.0,
    "result": "synthetic ordinary success",
}

#: A crashed executor: no result line at all.
CRASHED: Final = None

#: The settle `_drive` hands the driver, so a back-off is told apart from it.
SETTLE_S: Final = 45.0


class FakeClock:
    """A wall and a monotonic clock that advance only through `sleep`."""

    def __init__(self) -> None:
        """Start both clocks at fixed readings."""
        self.wall = 1_000_000.0
        self.mono = 0.0
        self.slept: list[float] = []

    def time(self) -> float:
        """Wall time, for the row stamp."""
        return self.wall

    def monotonic(self) -> float:
        """Deadline time."""
        return self.mono

    def sleep(self, seconds: float) -> None:
        """Record and advance instead of blocking."""
        self.slept.append(float(seconds))
        self.wall += float(seconds)
        self.mono += float(seconds)


def _worker_log(path: Path, result: dict[str, Any] | None, code: int) -> Path:
    """Write a synthetic worker log in the layout `run_lane.ps1` produces.

    The BOM is what `Out-File -Encoding utf8` emits under Windows PowerShell 5.1,
    and the reader has to survive it.
    """
    lines = ["lane start 2026-01-01T00:00:00 cwd=cs-lane-queue model=synthetic effort=high"]
    if result is not None:
        lines.append(json.dumps(result))
    lines.append(f"lane exit 2026-01-01T00:00:05 code={code}")
    path.write_bytes(b"\xef\xbb\xbf" + ("\r\n".join(lines) + "\r\n").encode("utf-8"))
    return path


def _launcher(tmp_path: Path, results: list[dict[str, Any] | None]):
    """A `launch` seam whose Nth launch leaves the Nth synthetic log behind."""
    fired: list[int] = []

    def launch(_lane: str, **_kw: Any) -> dict[str, Any]:
        n = len(fired)
        fired.append(n)
        result = results[n]
        code = 0 if result is not None and result.get("is_error") is False else 1
        log = _worker_log(tmp_path / f"lane_queue_{n}.log", result, code)
        return {"pid": 4242, "log": str(log.resolve())}

    return launch, fired


def _tree_sha():
    """A lane HEAD that moves on every read - every cycle that ran committed."""
    seen = {"n": 0}

    def tree_sha(_cwd: Any) -> str:
        seen["n"] += 1
        return f"commit-{seen['n']}"

    return tree_sha


def _drive(tmp_path: Path, results: list[dict[str, Any] | None], *, budget: int, **over: Any):
    """Run the REAL `run_loop` over scripted worker results, every seam stated."""
    clock = FakeClock()
    launch, fired = _launcher(tmp_path, results)
    lines: list[str] = []
    seams: dict[str, Any] = {
        "max_cycles": budget,
        "settle_s": SETTLE_S,
        "poll_s": 1,
        "acquire_retries": 1,
        "acquire": lambda _lane, **_kw: {"ok": True, "token": "T"},
        "release": lambda _token, **_kw: True,
        "launch": launch,
        "alive": lambda _pid: False,
        "proc_started": lambda _pid: 1.0,
        "stranger": lambda _pid, _started: False,
        "kill": lambda _pid: None,
        "ci_gate": False,
        "head_sha": lambda: "sha-unchanged",
        "tree_sha": _tree_sha(),
        "permit": lambda _lane, *_a, **_k: {
            "ok": True,
            "lane_scope": "fixture",
            "allowed": ("CS-FIXTURE",),
            "detail": "",
        },
        "claim_states": lambda _root=None, _now=None: {},
        "surface": lambda _worktree: {"unread": 0, "names": [], "more": 0, "reason": ""},
        "hold": contextlib.nullcontext,
        "cycle_log": tmp_path / "cycles.jsonl",
        "control_dir": tmp_path / "control",
        "worktree": "cs-lane-queue",
        "sleep": clock.sleep,
        "clock": clock.time,
        "monotonic": clock.monotonic,
        "emit": lines.append,
    }
    seams.update(over)
    summary = queue_loop.run_loop(**seams)
    written = (tmp_path / "cycles.jsonl").read_bytes().decode("utf-8")
    rows = [json.loads(line) for line in written.splitlines() if line.strip()]
    return summary, rows, written, clock, fired, lines


def test_cs1178_a_usage_limit_refusal_is_recorded_as_refused_not_run(tmp_path: Path) -> None:
    """THE ARM: the refusal's row says REFUSED, and it costs no cycle of the night.

    Against the driver as it stood, the refusal was the first `completed` row
    and the night's first cycle. Now the refused run is written down as what it
    was, the driver sleeps its back-off instead of the 45-second settle, and the
    two-cycle budget still buys two runs that happened.
    """
    results: list[dict[str, Any] | None] = [REFUSAL, ORDINARY_SUCCESS, ORDINARY_SUCCESS]
    summary, rows, written, clock, fired, _ = _drive(tmp_path, results, budget=2)

    refused = rows[0]
    assert refused["outcome"] != queue_loop.OUTCOME_COMPLETED, (
        "a usage-limit refusal was recorded as a run that happened"
    )
    assert refused["outcome"] == queue_loop.OUTCOME_USAGE_REFUSED
    assert refused["worker_ok"] is False
    assert refused["ok"] is False

    # NOT A CYCLE: the budget of two still bought two runs that happened, the
    # refused row carries no cycle number, and the summary counts it apart.
    ran = [row["outcome"] for row in rows[1:]]
    assert ran == [queue_loop.OUTCOME_COMPLETED] * 2, f"the refusal spent a cycle: {ran}"
    assert len(fired) == len(results), "the driver did not launch again after backing off"
    assert summary["stopped_by"] == queue_loop.STOPPED_BY_MAX_CYCLES
    numbers = [row["cycle"] for row in rows]
    assert numbers == [None, 1, 2], f"a refused run was numbered as a cycle: {numbers}"
    counted = (summary["cycles_run"], summary.get("usage_refusals"))
    assert counted == (2, 1), f"cycles_run and refusals {counted}"

    # THE BACK-OFF, and it is the FIRST wait after the refusal - not the settle.
    assert sum(clock.slept[:_POLLS]) == queue_loop.USAGE_LIMIT_BACKOFF_S, clock.slept[:4]
    assert queue_loop.USAGE_LIMIT_BACKOFF_S > SETTLE_S, "the back-off is no longer than the settle"

    # NOTHING THE WORKER WROTE reaches the durable row.
    assert NEEDLE not in written, "the worker's result text reached the written row"


def test_cs1178_the_control_ordinary_failures_and_crashes_are_still_runs(tmp_path: Path) -> None:
    """THE CONTROL, in the same run: only the refusal's shape is a refusal.

    An ordinary failed run (exit 1, error flag, real turns and cost), a 429 that
    arrived mid-run after real work, a crashed executor with no result at all,
    and a clean run are all recorded as runs that happened - so the repair did
    not simply relabel every exit 1.
    """
    results = [ORDINARY_FAILURE, MID_RUN_429, CRASHED, ORDINARY_SUCCESS]
    summary, rows, _, clock, fired, _ = _drive(tmp_path, results, budget=len(results))

    outcomes = [row["outcome"] for row in rows]
    assert outcomes == [queue_loop.OUTCOME_COMPLETED] * len(results), outcomes
    assert len(fired) == len(results)
    # ONLY THE SETTLE between cycles - no run here was backed off. Spelled as
    # the settle rather than as "not the back-off" so this control reads the
    # same against the driver before and after the repair.
    assert clock.slept == [SETTLE_S] * (len(results) - 1), f"a run was backed off: {clock.slept}"
    assert summary["cycles_run"] == len(results)


def test_cs1178_repeated_refusals_stop_the_night_with_their_own_word(tmp_path: Path) -> None:
    """THE LANE DOES NOT RE-ARM FOREVER on a limit that will not lift tonight.

    A weekly limit refuses every launch for days. Backing off without a bound
    would turn the night's budget into an unbounded series of one-turn probes;
    the consecutive-refusal limit ends it with a stop word and an exit code of
    its own, distinct from a lane that never started.
    """
    limit = queue_loop.MAX_CONSECUTIVE_USAGE_REFUSALS
    results: list[dict[str, Any] | None] = [REFUSAL] * (limit + 2)
    summary, rows, _, clock, fired, lines = _drive(tmp_path, results, budget=5)

    assert summary["stopped_by"] == queue_loop.STOPPED_BY_USAGE_LIMIT
    assert len(fired) == limit, f"launched {len(fired)} times against a limit of {limit}"
    assert [row["outcome"] for row in rows] == [queue_loop.OUTCOME_USAGE_REFUSED] * limit
    backed_off = sum(clock.slept)
    assert backed_off == queue_loop.USAGE_LIMIT_BACKOFF_S * (limit - 1), backed_off
    counted = (summary["cycles_run"], summary.get("usage_refusals"))
    assert counted == (0, limit), f"cycles_run and refusals {counted}"
    assert any("usage" in line for line in lines if line.startswith("queue-loop stop:"))

    table = queue_loop._STOP_EXIT  # noqa: SLF001 - the table under test
    code = table.get(queue_loop.STOPPED_BY_USAGE_LIMIT)
    assert code == queue_loop.EXIT_USAGE_LIMIT
    assert code != queue_loop.EXIT_CONSECUTIVE_LAUNCH_FAILURES


def test_cs1178_a_run_between_refusals_resets_the_count(tmp_path: Path) -> None:
    """CONSECUTIVE, not cumulative: one refusal between runs is a transient."""
    limit = queue_loop.MAX_CONSECUTIVE_USAGE_REFUSALS
    results: list[dict[str, Any] | None] = []
    for _ in range(limit):
        results += [REFUSAL] * (limit - 1) + [ORDINARY_SUCCESS]
    summary, rows, _, _, fired, _ = _drive(tmp_path, results, budget=limit)

    assert summary["stopped_by"] == queue_loop.STOPPED_BY_MAX_CYCLES
    assert len(fired) == len(results)
    completed = [row for row in rows if row["outcome"] == queue_loop.OUTCOME_COMPLETED]
    assert len(completed) == limit


#: The back-off is taken in polls of this many seconds, each fronted by a
#: stop-sentinel check.
_POLLS: Final = int(
    queue_loop.USAGE_LIMIT_BACKOFF_S // getattr(queue_loop, "USAGE_LIMIT_BACKOFF_POLL_S", 1)
)


def test_cs1178_a_budget_of_one_is_one_attempt(tmp_path: Path) -> None:
    """`--once` MEANS ONE ATTEMPT. A refusal ends it, recorded, with no back-off.

    Measured by the second adversary pass: with a budget of one and three
    refusals the driver launched three workers over two hours while the flag
    promised one cycle. A one-cycle night now makes exactly one attempt; the
    refusal is recorded as refused and ends the night on the usage-limit word.
    """
    summary, rows, _, clock, fired, _ = _drive(tmp_path, [REFUSAL] * 5, budget=1)

    assert len(fired) == 1, f"a budget of one launched {len(fired)} workers"
    assert clock.slept == [], f"a budget of one backed off: {sum(clock.slept)}s"
    assert [row["outcome"] for row in rows] == [queue_loop.OUTCOME_USAGE_REFUSED]
    assert summary["stopped_by"] == queue_loop.STOPPED_BY_USAGE_LIMIT
    counted = (summary["cycles_run"], summary.get("usage_refusals"))
    assert counted == (0, 1), f"cycles_run and refusals {counted}"


def test_cs1178_a_stop_sentinel_interrupts_the_back_off(tmp_path: Path) -> None:
    """THE BACK-OFF IS INTERRUPTIBLE, and the driver still owns the wait.

    An hour-long sleep would hold `QUEUE_STOP` unread for an hour. The wait is
    taken in short polls with the sentinel checked before each, so a sentinel
    written during the back-off ends the night within one poll and no further
    worker is launched.
    """
    control = tmp_path / "control"
    stop = control / "lanes" / "QUEUE_STOP"
    clock = FakeClock()

    def sleep(seconds: float) -> None:
        clock.sleep(seconds)
        stop.parent.mkdir(parents=True, exist_ok=True)
        stop.write_bytes(b"synthetic stop\n")

    summary, _, _, _, fired, _ = _drive(
        tmp_path, [REFUSAL, ORDINARY_SUCCESS], budget=2, sleep=sleep, control_dir=control
    )
    waited = sum(clock.slept)
    assert len(fired) == 1, f"a worker was launched after the stop: {len(fired)}"
    assert summary["stopped_by"] == "QUEUE_STOP", summary["stopped_by"]
    assert waited < queue_loop.USAGE_LIMIT_BACKOFF_S, f"the whole back-off was slept: {waited}"


def test_cs1178_a_refused_night_that_is_stopped_is_not_a_sentinel_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`main` reads zero cycles plus a sentinel as "the sentinel was already there".

    A night whose only runs were refused and which was then stopped mid-back-off
    ran zero cycles too, but the sentinel was NOT already there - it attempted.
    It must not exit as if it had refused to start.
    """
    summary = {
        "cycles_run": 0,
        "usage_refusals": 1,
        "stopped_by": "QUEUE_STOP",
        "records": [{"outcome": queue_loop.OUTCOME_USAGE_REFUSED, "commit": {"advanced": False}}],
    }
    said: list[str] = []
    monkeypatch.setattr(queue_loop, "run_loop", lambda **_kw: summary)
    monkeypatch.setattr(queue_loop, "_emit", said.append)

    class Singleton:
        def __call__(self):
            return contextlib.nullcontext()

    code = queue_loop.main(
        ["--once", "--control-dir", str(tmp_path / "control")], singleton=Singleton()
    )
    assert code != queue_loop.EXIT_STOP_SENTINEL, "a refused night read as never started"
    # AND IT SAYS WHY: the only runs were refused, so the exit is the usage-limit
    # code and a line names the refusals, rather than "0 cycle(s) ran" alone.
    assert code == queue_loop.EXIT_USAGE_LIMIT, f"a refusal-only night exited {code}"
    named = [line for line in said if "usage limit refusal" in line]
    assert named, "no line names the refusals that were the whole night"


def test_cs1178_the_reader_reads_only_an_absolute_log_and_never_raises(tmp_path: Path) -> None:
    """The default reader's boundaries, measured directly.

    A relative `log` is never opened - a fake launcher's placeholder name must
    not make a unit arm read whatever sits in the working directory - and a
    missing, empty or garbled log answers None rather than raising into a cycle.
    """
    reader = queue_loop._worker_result  # noqa: SLF001 - the reader under test
    log = _worker_log(tmp_path / "abs.log", REFUSAL, 1)
    got = reader(str(log.resolve()))
    assert isinstance(got, dict)
    assert got == REFUSAL, "the reader did not find the result line"

    assert reader(log.name) is None, "a relative log path was read"
    assert reader(None) is None
    assert reader(str((tmp_path / "absent.log").resolve())) is None
    # NESTED PAST THE PARSER'S RECURSION LIMIT, and still inside the tail: a
    # result-shaped line the decoder cannot finish must answer None, not raise.
    depth = 30000
    deep = tmp_path / "deep.log"
    deep.write_bytes(('{"a":' + ("[" * depth) + ("]" * depth) + "}" + "\n").encode("ascii"))
    assert deep.stat().st_size < queue_loop._RESULT_TAIL_BYTES  # noqa: SLF001 - the bound
    assert reader(str(deep.resolve())) is None, "a deeply nested line escaped the reader"
    garbled = tmp_path / "garbled.log"
    garbled.write_bytes(b"\xff\xfe{not json\n\x00\x01")
    assert reader(str(garbled.resolve())) is None


@pytest.mark.parametrize(
    ("result", "refused"),
    [
        (REFUSAL, True),
        ({**REFUSAL, "api_error_status": 529}, False),
        ({**REFUSAL, "api_error_status": "429"}, False),
        ({**REFUSAL, "is_error": False}, False),
        ({**REFUSAL, "num_turns": 2}, False),
        ({**REFUSAL, "total_cost_usd": 0.01}, False),
        (ORDINARY_FAILURE, False),
        (MID_RUN_429, False),
        (None, False),
        ("429", False),
    ],
)
def test_cs1178_only_the_refusal_shape_classifies_as_a_refusal(
    result: object, *, refused: bool
) -> None:
    """Every field of the shape is load-bearing, and each is graded alone."""
    assert queue_loop._is_usage_refusal(result) is refused  # noqa: SLF001 - the classifier


# ===========================================================================
# The runner's half: a REAL run_lane.ps1 writes the log the driver reads
# ===========================================================================

#: The runner under test - the file the launcher really spawns.
RUNNER_SOURCE: Final = ROOT / "ops" / "loop" / "run_lane.ps1"

#: A wedged child fails the arm rather than hanging the run.
_CHILD_TIMEOUT_S: Final = 120.0

#: Characters `cmd.exe` would interpret inside an `echo`. The shim's JSON line
#: must hold none of them, or the arm would grade cmd's quoting, not the runner.
_CMD_SPECIALS: Final = frozenset("&|<>^%")

#: Long enough that a runner or an `Out-File` that wrapped or truncated its lines
#: at a console width would split the JSON and make it unparseable.
_PADDING: Final = "x" * 600


def _powershell() -> str:
    """The interpreter, resolved from PATH and never named as a bare string."""
    tools = ROOT / "tools"
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    from toolpath import resolve_tool  # noqa: PLC0415 - tools/ is not a package

    shell = resolve_tool("powershell")
    if shell is None:
        pytest.skip("powershell could not be resolved from PATH")
    return str(shell)


def _shim(tmp_path: Path, result: dict[str, Any], code: int) -> tuple[Path, Path]:
    """A `claude` that records its argv, prints ONE result line and exits `code`.

    NO REAL CLI IS EVER INVOKED: PATH is rebuilt from this directory and the
    system directory, so `claude` resolves to this batch file or to nothing.
    """
    line = json.dumps(result, separators=(",", ":"))
    unsafe = sorted(set(line) & _CMD_SPECIALS)
    assert unsafe == [], f"the shim's JSON holds cmd specials {unsafe}"
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir(parents=True, exist_ok=True)
    # RELATIVE, so no path is baked into the shim: the runner sets its location
    # to the tree before it invokes the CLI, so this lands in the tree.
    argv_file = tmp_path / "tree" / "argv.txt"
    (shim_dir / "claude.cmd").write_bytes(
        b"@echo off\r\n"
        + b"echo %* > argv.txt\r\n"
        + b"echo "
        + line.encode("ascii")
        + b"\r\nexit /b "
        + str(code).encode("ascii")
        + b"\r\n"
    )
    return shim_dir, argv_file


def _run_real_runner(tmp_path: Path, shim_dir: Path) -> Path:
    """Run the REAL runner with PATH rebuilt from the shim, and return its log."""
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(b"# a prompt the shim never reads\n")
    tree = tmp_path / "tree"
    tree.mkdir(exist_ok=True)
    log = tmp_path / "lane_queue_real.log"
    env = dict(os.environ)
    system_root = env.get("SYSTEMROOT") or env.get("SystemRoot") or "C:\\Windows"
    env["PATH"] = f"{shim_dir}{os.pathsep}{Path(system_root) / 'System32'}"
    env.pop("ANTHROPIC_API_KEY", None)
    subprocess.run(
        [
            _powershell(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(RUNNER_SOURCE),
            "-PromptFile",
            str(prompt),
            "-Cwd",
            str(tree),
            "-Log",
            str(log),
        ],
        capture_output=True,
        check=False,
        timeout=_CHILD_TIMEOUT_S,
        env=env,
    )
    return log


def _real_log(tmp_path: Path, result: dict[str, Any], code: int) -> tuple[Path, str]:
    """A log written by the real runner over a shim, and the argv the shim saw."""
    shim_dir, argv_file = _shim(tmp_path, result, code)
    log = _run_real_runner(tmp_path, shim_dir)
    ran = argv_file.is_file()
    assert ran, "the shim never ran - the arm grades nothing"
    argv = argv_file.read_bytes().decode("ascii", errors="replace")
    return log, argv


@pytest.mark.skipif(os.name != "nt", reason="run_lane.ps1 is driven by Windows PowerShell")
def test_cs1178_a_real_runner_refusal_log_is_recognised_end_to_end(tmp_path: Path) -> None:
    """THE RUNNER ASKS FOR JSON, and the log it writes is one the driver reads.

    Before this, the runner invoked the CLI in its default TEXT mode, which
    emits no result object, so `_worker_result` answered None on every real log
    and the driver's refusal check could never fire. Here the real runner runs
    over a shim that prints a refusal-shaped result line, and the driver - fed
    that very file - records no run and backs off.
    """
    refusal = {**REFUSAL, "result": f"synthetic usage limit refusal {_PADDING}"}
    log, argv = _real_log(tmp_path / "refused", refusal, 1)
    control_log, _ = _real_log(tmp_path / "ordinary", ORDINARY_FAILURE, 1)

    # THE RUNNER'S HALF: the CLI was asked for its JSON result.
    asked = "--output-format json" in argv
    assert asked, "the runner did not ask the CLI for JSON output"

    # THE LOG KEEPS A HUMAN-READABLE BODY and the machine-readable line, and
    # still ends on the runner's own exit line carrying the worker's code.
    lines = [
        line.strip()
        for line in log.read_bytes().decode("utf-8-sig", errors="replace").splitlines()
        if line.strip()
    ]
    first, last = lines[0], lines[-1]
    assert first.startswith("lane start "), "the header is gone"
    assert last.startswith("lane exit "), "the exit line is gone"
    assert last.endswith("code=1"), "the exit line does not carry the worker's code"
    readable = any(line.startswith("synthetic usage limit refusal") for line in lines)
    assert readable, "the result text was not written as a readable line"
    parsed = queue_loop._worker_result(str(log.resolve()))  # noqa: SLF001 - the reader
    assert parsed == refusal, "the JSON line did not survive the runner intact"

    # THE DRIVER'S HALF, over the runner's own file: refused, not run, backed off.
    logs = [log, control_log, control_log]
    fired: list[int] = []

    def launch(_lane: str, **_kw: Any) -> dict[str, Any]:
        fired.append(len(fired))
        return {"pid": 4242, "log": str(logs[len(fired) - 1].resolve())}

    summary, rows, _, clock, _, _ = _drive(tmp_path, [], budget=2, launch=launch)
    outcomes = [row["outcome"] for row in rows]
    assert outcomes == [
        queue_loop.OUTCOME_USAGE_REFUSED,
        queue_loop.OUTCOME_COMPLETED,
        queue_loop.OUTCOME_COMPLETED,
    ], f"outcomes {outcomes}"
    assert sum(clock.slept[:_POLLS]) == queue_loop.USAGE_LIMIT_BACKOFF_S, clock.slept[:4]
    assert summary["stopped_by"] == queue_loop.STOPPED_BY_MAX_CYCLES
