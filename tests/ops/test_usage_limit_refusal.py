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
REAL runner over a shim `python` standing where the fleet kit's interpreter
stands (CS-1231 slice C), printing the line the REAL kit's command line prints
for that result, and feeds the driver the log the runner wrote.

Only the runner half spawns a process. No arm sleeps or reads the live channel,
and the one lock taken is the in-process kit's, on a budget file under tmp_path.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# A PLAIN IMPORT, never importorskip: a missing driver is a COLLECTION error.
from ops.fleet_kit import fleet_headless as kit  # noqa: E402
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


def _drive(
    tmp_path: Path,
    results: list[dict[str, Any] | None],
    *,
    budget: int,
    loop: Any = None,
    **over: Any,
):
    """Run the REAL `run_loop` over scripted worker results, every seam stated.

    `loop` is the `run_loop` to call, for an arm that has patched the module's
    own name so `main` reaches this one; None calls the module's.
    """
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
    summary = (queue_loop.run_loop if loop is None else loop)(**seams)
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


class _Closable:
    """What the fake connect hands back: something the kit can close."""

    def close(self) -> None:
        """Nothing to close."""


def _kit_line(tmp_path: Path, result: dict[str, Any], code: int) -> tuple[str, list[str]]:
    """The line the REAL kit's command line prints when its CLI printed `result`.

    The kit's own `main` and `spawn` run in this process against a root under
    `tmp_path`; the CLI is a fake run that prints `result` and exits `code`,
    and the proxy URL, the connect and the executable are injected, so nothing
    live is read or written.

    Returns:
        The printed line, and the CLI argv the kit built.
    """
    started: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        started.append(list(argv))
        return subprocess.CompletedProcess(argv, code, json.dumps(result), "")

    def spawn_fn(root: Any, code: Any, prompt: Any, **kwargs: Any) -> dict[str, Any]:
        line: dict[str, Any] = kit.spawn(
            root,
            code,
            prompt,
            run=fake_run,
            url_source=lambda: "http://127.0.0.1:9",
            connect=lambda *_args, **_kwargs: _Closable(),
            exe_source=lambda: "synthetic-claude",
            **kwargs,
        )
        return line

    root = tmp_path / "kit-root"
    root.mkdir(parents=True, exist_ok=True)
    printed = io.StringIO()
    exit_code = kit.main(
        ["spawn", "--root", str(root), "--code", "CS", "--note", "synthetic", "--kind", "build"],
        spawn_fn=spawn_fn,
        stdin=io.StringIO("# synthetic prompt\n"),
        stdout=printed,
    )
    assert exit_code == kit.CLI_OK, f"the in-process kit answered {exit_code}"
    assert len(started) == 1, "the in-process kit did not start one CLI"
    return printed.getvalue().strip(), started[0]


def _shim(tmp_path: Path, result: dict[str, Any], code: int) -> tuple[Path, Path, list[str]]:
    """A `python` that records its argv, prints the kit's ONE line and exits 0.

    NO REAL KIT AND NO REAL CLI IS EVER INVOKED by the runner: PATH is rebuilt
    from this directory and the system directory, so `python` resolves to this
    batch file or to nothing. The kit exits 0 for a run that ENDED; the CLI's
    own exit `code` rides in the line's `rc`.
    """
    line, cli_argv = _kit_line(tmp_path, result, code)
    unsafe = sorted(set(line) & _CMD_SPECIALS)
    assert unsafe == [], f"the shim's JSON holds cmd specials {unsafe}"
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir(parents=True, exist_ok=True)
    # RELATIVE, so no path is baked into the shim: the runner sets its location
    # to the tree before it invokes the kit, so this lands in the tree.
    argv_file = tmp_path / "tree" / "argv.txt"
    (shim_dir / "python.cmd").write_bytes(
        b"@echo off\r\n"
        + b"echo %* > argv.txt\r\n"
        + b"echo "
        + line.encode("ascii")
        + b"\r\nexit /b 0\r\n"
    )
    return shim_dir, argv_file, cli_argv


def _run_real_runner(tmp_path: Path, shim_dir: Path) -> Path:
    """Run the REAL runner with PATH rebuilt from the shim, and return its log."""
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(b"# a prompt the shim never reads\n")
    tree = tmp_path / "tree"
    tree.mkdir(exist_ok=True)
    log = tmp_path / "lane_queue_real.log"
    _run_runner_to(RUNNER_SOURCE, prompt, tree, log, shim_dir)
    return log


def _run_runner_to(runner: Path, prompt: Path, tree: Path, log: Path, shim_dir: Path) -> None:
    """Run `runner` - the REAL runner - over the shim PATH, writing `log`."""
    env = dict(os.environ)
    system_root = env.get("SYSTEMROOT") or env.get("SystemRoot") or "C:\\Windows"
    env["PATH"] = f"{shim_dir}{os.pathsep}{Path(system_root) / 'System32'}"
    env.pop("ANTHROPIC_API_KEY", None)
    # CS-1225 - the runner refuses an ANTHROPIC_BASE_URL outside the loopback
    # allowlist before it looks for the CLI. A SYNTHETIC value in that shape,
    # so no arm depends on this machine's route; the stub never connects.
    env["ANTHROPIC_BASE_URL"] = "http://localhost:3456/synthetic/route"
    subprocess.run(
        [
            _powershell(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(runner),
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


def _real_log(tmp_path: Path, result: dict[str, Any], code: int) -> tuple[Path, str, list[str]]:
    """A log written by the real runner over a shim, and what it was handed.

    Returns:
        The log, the argv the shim saw, and the CLI argv the in-process kit
        built for the same result.
    """
    shim_dir, argv_file, cli_argv = _shim(tmp_path, result, code)
    log = _run_real_runner(tmp_path, shim_dir)
    ran = argv_file.is_file()
    assert ran, "the shim never ran - the arm grades nothing"
    argv = argv_file.read_bytes().decode("ascii", errors="replace")
    return log, argv, cli_argv


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
    log, argv, cli_argv = _real_log(tmp_path / "refused", refusal, 1)
    control_log, _, _ = _real_log(tmp_path / "ordinary", ORDINARY_FAILURE, 1)

    # THE RUNNER'S HALF: the runner ran the fleet kit's spawn command line
    # (CS-1231 slice C), and the kit asked the CLI for its JSON result.
    through_kit = "fleet_headless.py" in argv and " spawn " in argv
    assert through_kit, "the runner did not run the kit's spawn command line"
    at = cli_argv.index("--output-format") if "--output-format" in cli_argv else -1
    asked = at >= 0 and cli_argv[at + 1 : at + 2] == ["json"]
    assert asked, "the kit did not ask the CLI for JSON output"

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


# ===========================================================================
# CS-1231 slice C - THE KIT'S ENDINGS, read off the runner's log by the driver
#
# The runner starts the fleet kit, and the kit can end a run three ways the
# CLI's result object cannot show: its own timeout (exit 4), a refusal (exit 3,
# with a code), and a bad command line (exit 2). The runner writes ONE line
# naming the ending IMMEDIATELY before its exit line, and the driver reads only
# that line - so worker text earlier in the log cannot forge it. The words below
# are literals on purpose: an arm that compared against a constant the repair
# introduces would fail on the base with an AttributeError, not for its reason.
# ===========================================================================

_STAMP: Final = "2026-01-01T00:00:05"

#: The kit's own timeout, as the runner records it.
_TIMEOUT_TAIL: Final = (f"lane timeout {_STAMP} kit_exit=4", f"lane exit {_STAMP} code=4")

#: The fleet kit's budget refusal and its usage-limit halt, by code.
_BUDGET_CODE: Final = "budget-spent"
_LIMIT_CODE: Final = "fallback-halted"

#: Planted where the driver must never copy from: the kit's status file.
_STATUS_NEEDLE: Final = "cs1231c-status-needle"


def _refused_tail(code: str) -> tuple[str, str]:
    """A kit refusal, as the runner records it: the code, then the exit line."""
    return (f"lane refused {_STAMP} kit_code={code}", f"lane exit {_STAMP} code=3")


def _ending_log(path: Path, tail: tuple[str, ...], *, before: tuple[str, ...] = ()) -> Path:
    """A runner log in `run_lane.ps1`'s layout whose LAST lines are `tail`."""
    lines = [
        "lane start 2026-01-01T00:00:00 cwd=cs-lane-queue model=synthetic effort=high",
        *before,
        *tail,
    ]
    path.write_bytes(b"\xef\xbb\xbf" + ("\r\n".join(lines) + "\r\n").encode("utf-8"))
    return path


def _ok_log(path: Path) -> Path:
    """An ordinary run's log - the control every refusal arm is told apart from."""
    return _worker_log(path, ORDINARY_SUCCESS, 0)


def _iso(epoch: float) -> str:
    """An offset-bearing ISO stamp, the shape the kit writes `cap_frees_at` in."""
    return datetime.fromtimestamp(epoch, tz=UTC).isoformat(timespec="seconds")


#: The wall clock `FakeClock` starts at, so a status file can be written against it.
_WALL: Final = FakeClock().wall


def _status(
    control: Path,
    *,
    frees_in: float | None,
    used: int = 120,
    cap: int = 120,
    now: float = _WALL,
) -> Path:
    """The kit's status file in `control`, with the run budget's fields set.

    `frees_in` is seconds after `now` (the fake clock's start by default), or
    None for no stamp.
    """
    doc = {
        "schema": 1,
        "code": "CS",
        "state": "limit",
        "task": "Turn Limit Reached",
        "runs_in_window": used,
        "runs_cap": cap,
        "window_s": 86400,
        "cap_frees_at": None if frees_in is None else _iso(now + frees_in),
        "reason": f"synthetic {_STATUS_NEEDLE}",
    }
    control.mkdir(parents=True, exist_ok=True)
    path = control / "inbox_status.json"
    path.write_bytes(json.dumps(doc).encode("ascii"))
    return path


def _early_exit(log: Path | None):
    """The launcher's refusal for a runner that exited inside its 2.0 s grace.

    Built as `launch_lane` re-raises it: the reason word, the wait it consumed,
    and the log it had chosen for that runner (None when it had chosen none).
    """
    exc = queue_loop.lane_launcher.LaneLaunchError(
        "the runner exited 3 within 2.0s of starting, so no worker is behind this lane",
        reason="runner_exited_early",
        waited_s=0.24,
    )
    exc.log = None if log is None else str(log.resolve())
    return exc


def _launches(items: list[Any]):
    """A `launch` seam: a Path leaves that log behind; ("early", log) exits in the grace.

    ("early", log) raises the launcher's own refusal for a runner that exited
    inside its 2.0 s liveness grace - the path EVERY fast kit refusal takes
    (MEASURED by the adversary: about 0.24 s) - carrying that runner's log.
    """
    fired: list[dict[str, Any]] = []

    def launch(lane: str, **kw: Any) -> dict[str, Any]:
        fired.append({"lane": lane, **kw})
        item = items[len(fired) - 1]
        if isinstance(item, tuple):
            raise _early_exit(item[1])
        assert isinstance(item, Path)
        return {"pid": 4242, "log": str(item.resolve())}

    return launch, fired


def test_l1_a_kit_timeout_ending_is_recorded_timeout_killed_not_completed(tmp_path: Path) -> None:
    """THE HIGH FINDING: the kit's own timeout ended the run, so it is a timeout.

    The kit kills the CLI's tree at its `--timeout` and exits 4; the runner
    exits on its own a moment later, so the driver's pid probe sees a worker
    that EXITED, and before this repair the cycle read `completed`.
    """
    launch, _ = _launches([_ending_log(tmp_path / "t.log", _TIMEOUT_TAIL)])
    _, rows, _, _, _, _ = _drive(tmp_path, [], budget=1, launch=launch)
    outcome = rows[0]["outcome"]
    assert outcome == "timeout_killed", f"a kit timeout was recorded as {outcome!r}"
    assert rows[0]["worker_ok"] is False


def test_l1_control_a_marker_in_worker_text_is_not_the_runners_ending(tmp_path: Path) -> None:
    """THE CONTROL: only the line immediately before the exit line is read.

    A worker's own words are written ahead of its result object, so a
    timeout-shaped line in them is never adjacent to the exit line - and a run
    whose CLI exited 4 itself is still a run that ended.
    """
    forged = (f"lane timeout {_STAMP} kit_exit=4", json.dumps(ORDINARY_SUCCESS))
    log = _ending_log(tmp_path / "f.log", (f"lane exit {_STAMP} code=4",), before=forged)
    launch, _ = _launches([log])
    _, rows, _, _, _, _ = _drive(tmp_path, [], budget=1, launch=launch)
    outcome = rows[0]["outcome"]
    assert outcome == "completed", f"a forged marker was read as the ending: {outcome!r}"


def test_l2_a_post_grace_budget_refusal_is_not_a_cycle_and_backs_off_until_the_cap_frees(
    tmp_path: Path,
) -> None:
    """THE MEDIUM FINDING, after the grace: a spent budget is refused, not run.

    The row says so, costs no cycle of the night, and the driver waits until the
    kit's cap frees - `cap_frees_at` in the kit's status file, plus one poll -
    rather than the fixed usage-limit hour or the 45-second settle.
    """
    control = tmp_path / "control"
    _status(control, frees_in=5000)
    logs = [
        _ending_log(tmp_path / "r.log", _refused_tail(_BUDGET_CODE)),
        _ok_log(tmp_path / "ok1.log"),
        _ok_log(tmp_path / "ok2.log"),
    ]
    launch, fired = _launches(list(logs))
    summary, rows, written, clock, _, _ = _drive(tmp_path, [], budget=2, launch=launch)
    outcomes = [row["outcome"] for row in rows]
    assert outcomes == ["budget_spent", "completed", "completed"], f"outcomes {outcomes}"
    assert rows[0]["cycle"] is None, "a refused start was numbered as a cycle"
    assert rows[0]["worker_ok"] is False
    waited = sum(clock.slept) - SETTLE_S
    expected = 5000 + queue_loop.USAGE_LIMIT_BACKOFF_POLL_S
    assert waited == expected, f"the back-off was {waited}s, not {expected}s"
    counted = (summary["cycles_run"], summary["stopped_by"], len(fired))
    assert counted == (2, queue_loop.STOPPED_BY_MAX_CYCLES, 3), f"summary {counted}"
    leaked = _STATUS_NEEDLE in written
    assert leaked is False, "the kit's status text reached the written row"


@pytest.mark.parametrize(
    ("tail", "word"),
    [
        (_refused_tail(_BUDGET_CODE), "budget_spent"),
        (_refused_tail(_LIMIT_CODE), "usage_refused"),
        (_refused_tail("blocked"), "launch_failed"),
        (_refused_tail("refused"), "launch_failed"),
    ],
    ids=["budget-spent", "fallback-halted", "blocked", "refused"],
)
def test_r1_an_early_exit_kit_refusal_is_read_off_the_runners_log(
    tmp_path: Path, tail: tuple[str, str], word: str
) -> None:
    """R1: a fast kit refusal ALWAYS dies inside the grace, so the log is read there.

    The launcher hands back the log it chose for the runner; the runner's ending
    line in it names the kit's code, and the code decides the outcome - the same
    mapping as after the grace, never the bare `launch_failed` of a lane fault.
    """
    log = _ending_log(tmp_path / "e.log", (*tail, f"lane abort {_STAMP} code=none reason=x"))
    _status(tmp_path / "control", frees_in=600)
    launch, _ = _launches([("early", log)])
    _, rows, _, _, _, _ = _drive(tmp_path, [], budget=1, launch=launch)
    outcome = rows[0]["outcome"]
    assert outcome == word, f"an early-exit {tail[0][-30:]!r} read {outcome!r}"


def test_r1_early_exit_budget_refusals_never_end_the_night_as_launch_failures(
    tmp_path: Path,
) -> None:
    """Three in a row end the night on the usage-limit word, not on a lane fault."""
    _status(tmp_path / "control", frees_in=600)
    log = _ending_log(tmp_path / "e.log", _refused_tail(_BUDGET_CODE))
    launch, fired = _launches([("early", log)] * 5)
    summary, rows, _, _, _, _ = _drive(tmp_path, [], budget=5, launch=launch)
    limit = queue_loop.MAX_CONSECUTIVE_USAGE_REFUSALS
    outcomes = [row["outcome"] for row in rows]
    assert outcomes == ["budget_spent"] * limit, f"outcomes {outcomes}"
    stopped = summary["stopped_by"]
    assert stopped == queue_loop.STOPPED_BY_USAGE_LIMIT, f"the night stopped on {stopped!r}"
    assert len(fired) == limit


def test_r1_an_early_exit_kit_halt_stops_the_night_cleanly(tmp_path: Path) -> None:
    """R1: `halted` is a declared stop sentinel standing - a clean stop, not a fault.

    Before the repair three of these were three `launch_failed` rows and a night
    ended on `consecutive_launch_failures`.
    """
    log = _ending_log(tmp_path / "h.log", _refused_tail("halted"))
    launch, fired = _launches([("early", log)] * 5)
    summary, rows, _, _, _, _ = _drive(tmp_path, [], budget=5, launch=launch)
    outcomes = [row["outcome"] for row in rows]
    assert outcomes == ["kit_halted"], f"outcomes {outcomes}"
    stopped = (summary["stopped_by"], len(fired), rows[0]["cycle"])
    assert stopped == ("kit_halted", 1, None), f"stopped {stopped}"


class _NoMutex:
    """Stands in for the driver mutex: takes no OS handle."""

    def __call__(self) -> contextlib.AbstractContextManager[None]:
        """Hand back a context manager that holds nothing."""
        return contextlib.nullcontext()


def test_r3_a_night_halted_at_its_first_start_ran_no_cycle_and_exits_as_a_stop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A halted start is not a cycle, so the night exits as a sentinel stop.

    THROUGH `main`, over the real `run_loop`: a night whose only start the kit
    halted ran ZERO cycles, and `main` reads that as "a stop file was there" -
    counted as a cycle instead, it would read as a night that shipped nothing.
    """
    log = _ending_log(tmp_path / "h.log", _refused_tail("halted"))
    launch, _ = _launches([("early", log)])
    real = queue_loop.run_loop
    seen: dict[str, Any] = {}

    def night(**_kw: Any) -> dict[str, Any]:
        summary, _, _, _, _, _ = _drive(tmp_path, [], budget=1, loop=real, launch=launch)
        seen.update(summary)
        return dict(summary)

    monkeypatch.setattr(queue_loop, "run_loop", night)
    monkeypatch.setattr(queue_loop, "_emit", lambda _line: None)
    code = queue_loop.main(
        ["--once", "--control-dir", str(tmp_path / "control")], singleton=_NoMutex()
    )
    ran = seen.get("cycles_run")
    assert ran == 0, f"a halted start was counted as {ran} cycle(s)"
    assert code == queue_loop.EXIT_STOP_SENTINEL, f"a halted night exited {code}"


def test_r3_a_declared_sentinel_placed_during_a_back_off_ends_it_within_a_poll(
    tmp_path: Path,
) -> None:
    """The back-off reads the TREE's declared sentinels too, not only the driver's own.

    The declared sentinel appears once the back-off has begun - the first sleep
    there is - so only a back-off that reads it stops inside the hour.
    """
    clock = FakeClock()

    def kit_halt() -> str | None:
        return "kit_halted" if clock.slept else None

    summary, _, _, _, fired, _ = _drive(
        tmp_path,
        [REFUSAL, ORDINARY_SUCCESS],
        budget=2,
        kit_halt=kit_halt,
        sleep=clock.sleep,
        clock=clock.time,
        monotonic=clock.monotonic,
    )
    verdict = (summary["stopped_by"], len(fired))
    assert verdict == ("kit_halted", 1), f"night {verdict}"
    waited = sum(clock.slept)
    assert waited < queue_loop.USAGE_LIMIT_BACKOFF_S, f"the whole back-off was slept: {waited}s"


def test_r1_control_an_early_exit_with_no_kit_ending_is_still_a_launch_failure(
    tmp_path: Path,
) -> None:
    """THE CONTROL: an early exit whose log names no kit ending stays a lane fault.

    The status file says the budget is spent, and that is NOT evidence the
    start was refused for it: only the runner's own line is read.
    """
    _status(tmp_path / "control", frees_in=600)
    log = _ending_log(tmp_path / "n.log", (f"lane exit {_STAMP} code=1",))
    launch, _ = _launches([("early", log), ("early", None)])
    _, rows, _, _, _, _ = _drive(tmp_path, [], budget=2, settle_s=0, launch=launch)
    outcomes = [row["outcome"] for row in rows]
    assert outcomes == ["launch_failed", "launch_failed"], f"outcomes {outcomes}"


def test_r3_only_an_early_exit_reads_the_runners_log(tmp_path: Path) -> None:
    """A launch that failed BEFORE a runner ran is a lane fault, whatever a log says.

    The launcher hands its chosen log back on every refusal; only
    `runner_exited_early` means a runner wrote it. Here the spawn itself failed,
    and a stale log at that path names a spent budget - which must not be read.
    """
    log = _ending_log(tmp_path / "stale.log", _refused_tail(_BUDGET_CODE))
    exc = queue_loop.lane_launcher.LaneLaunchError(
        "spawn failed: synthetic", reason="spawn_failed", waited_s=None
    )
    exc.log = str(log.resolve())

    def launch(_lane: str, **_kw: Any) -> dict[str, Any]:
        raise exc

    _, rows, _, _, _, _ = _drive(tmp_path, [], budget=1, launch=launch)
    outcome = rows[0]["outcome"]
    assert outcome == "launch_failed", f"a spawn failure read its stale log as {outcome!r}"


def test_r3_a_timeout_line_before_an_exit_line_without_the_kits_code_is_not_a_timeout(
    tmp_path: Path,
) -> None:
    """The timeout line counts only beside the kit's timeout code on the exit line."""
    tail = (f"lane timeout {_STAMP} kit_exit=4", f"lane exit {_STAMP} code=0")
    launch, _ = _launches([_ending_log(tmp_path / "t0.log", tail)])
    _, rows, _, _, _, _ = _drive(tmp_path, [], budget=1, launch=launch)
    outcome = rows[0]["outcome"]
    assert outcome == "completed", f"a timeout line beside exit code 0 read {outcome!r}"


def test_l2_repeated_budget_refusals_end_the_night_on_the_usage_limit_word(
    tmp_path: Path,
) -> None:
    """Bounded: a cap that will not free tonight ends the night, with its own word."""
    _status(tmp_path / "control", frees_in=60)
    limit = queue_loop.MAX_CONSECUTIVE_USAGE_REFUSALS
    logs = [_ending_log(tmp_path / f"r{n}.log", _refused_tail(_BUDGET_CODE)) for n in range(5)]
    launch, fired = _launches(list(logs))
    summary, rows, _, _, _, _ = _drive(tmp_path, [], budget=5, launch=launch)
    outcomes = [row["outcome"] for row in rows]
    assert outcomes == ["budget_spent"] * limit, f"outcomes {outcomes}"
    stopped = (summary["stopped_by"], len(fired), summary["cycles_run"])
    assert stopped == (queue_loop.STOPPED_BY_USAGE_LIMIT, limit, 0), f"stopped {stopped}"


def test_l2_other_kit_refusal_codes_are_launch_failures_not_completions(tmp_path: Path) -> None:
    """Any other kit refusal is a start that did not happen - never `completed`."""
    logs = [_ending_log(tmp_path / "p.log", _refused_tail("proxy-unreachable"))]
    launch, _ = _launches(list(logs))
    _, rows, written, _, _, _ = _drive(tmp_path, [], budget=1, launch=launch)
    outcome = rows[0]["outcome"]
    assert outcome == "launch_failed", f"a kit refusal was recorded as {outcome!r}"
    named = "proxy-unreachable" in rows[0]["detail"]
    assert named, "the row does not name the kit's refusal code"
    assert NEEDLE not in written


def test_l2_a_refusal_code_outside_the_kits_vocabulary_is_written_as_unknown(
    tmp_path: Path,
) -> None:
    """The driver renders only its own copy of the kit's words, never the log's."""
    planted = "cs-planted-code"
    logs = [_ending_log(tmp_path / "u.log", _refused_tail(planted))]
    launch, _ = _launches(list(logs))
    _, rows, written, _, _, lines = _drive(tmp_path, [], budget=1, launch=launch)
    outcome = rows[0]["outcome"]
    assert outcome == "launch_failed", f"an unknown refusal read {outcome!r}"
    leaked = planted in written or any(planted in line for line in lines)
    assert leaked is False, "a code outside the kit's vocabulary reached the row"


@pytest.mark.parametrize(
    ("ending", "word"),
    [
        (_refused_tail(_LIMIT_CODE), "usage_refused"),
        (None, "usage_refused"),
    ],
    ids=["kit-fallback-halted", "cli-429"],
)
def test_a_usage_limit_refusal_stops_the_lane_with_no_hop_of_its_own(
    tmp_path: Path, ending: tuple[str, str] | None, word: str
) -> None:
    """FLEET item 10: a usage limit is waited out, then the night ends - no fallback.

    Both shapes of a usage limit - the CLI's own 429 refusal and the kit's
    `fallback-halted` (the limit holds on every route the kit may use) - are
    refused-not-run rows, backed off by the fixed hour, and end the night on the
    usage-limit word. Every launch is handed exactly the seams it always was: no
    route, mode, model or account is chosen by the lane, so the ONLY hop is the
    one the kit's own route file arms, inside the kit.
    """
    limit = queue_loop.MAX_CONSECUTIVE_USAGE_REFUSALS
    logs = []
    for n in range(5):
        path = tmp_path / f"l{n}.log"
        logs.append(_ending_log(path, ending) if ending else _worker_log(path, REFUSAL, 1))
    launch, fired = _launches(list(logs))
    summary, rows, _, clock, _, _ = _drive(tmp_path, [], budget=5, launch=launch)
    outcomes = [row["outcome"] for row in rows]
    assert outcomes == [word] * limit, f"outcomes {outcomes}"
    assert summary["stopped_by"] == queue_loop.STOPPED_BY_USAGE_LIMIT
    backed_off = sum(clock.slept)
    assert backed_off == queue_loop.USAGE_LIMIT_BACKOFF_S * (limit - 1), backed_off
    handed = sorted({key for call in fired for key in call})
    assert handed == ["lane", "run_id", "token"], f"a launch was handed {handed}"
    lanes = {call["lane"] for call in fired}
    assert lanes == {queue_loop.LANE}, f"the lane changed under a limit: {sorted(lanes)}"


#: The kit's route-changing API, which neither the driver nor the runner may name.
_ROUTE_API: Final = frozenset(
    {"write_route", "start_fallback", "effective_route", "fallback_state_path", "route_show"}
)


def test_neither_the_driver_nor_the_runner_names_the_kits_route_api() -> None:
    """The static half of the arm above: no hop is even reachable from the lane.

    The driver's code names no kit function that moves a route, and the
    runner's code - comments dropped - passes no fallback flag and runs no kit
    subcommand but `spawn`.
    """
    tree = ast.parse((ROOT / "ops" / "loop" / "queue_loop.py").read_text(encoding="utf-8"))
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    names |= {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    named = sorted(names & _ROUTE_API)
    assert named == [], f"the driver names the kit's route API: {named}"
    text = RUNNER_SOURCE.read_bytes().decode("ascii")
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    flagged = "fallback" in code.lower()
    assert flagged is False, "the runner's code carries a fallback flag"
    subcommands = re.findall(r'"\$kit",\s*"([a-z]+)"', code)
    assert subcommands == ["spawn"], f"the runner runs kit subcommands {subcommands}"


@pytest.mark.parametrize(
    ("frees_in", "expected"),
    [
        (5000.0, 5000 + 30),
        (-100.0, 30),
        (10 * 86400.0, 86400),
        (None, 3600),
    ],
    ids=["future", "past", "beyond-a-window", "no-stamp"],
)
def test_l2_the_budget_back_off_reads_cap_frees_at_and_clamps(
    tmp_path: Path, frees_in: float | None, expected: int
) -> None:
    """Until the cap frees plus one poll, inside [one poll, one window], else an hour."""
    _status(tmp_path, frees_in=frees_in)
    status = queue_loop._kit_status(tmp_path)  # noqa: SLF001 - the reader under test
    got = queue_loop._budget_back_off_s(status, _WALL)  # noqa: SLF001 - the clamp under test
    assert got == expected


@pytest.mark.parametrize(
    "planted",
    [b"{not json", b"[]", b'{"cap_frees_at": "2026-01-01T00:00:00"}', b'{"cap_frees_at": 7}'],
    ids=["garbled", "not-an-object", "naive-stamp", "not-a-string"],
)
def test_l2_an_unusable_status_file_backs_off_the_fixed_hour(
    tmp_path: Path, planted: bytes
) -> None:
    """A stamp the driver cannot place in time is never guessed at."""
    (tmp_path / "inbox_status.json").write_bytes(planted)
    status = queue_loop._kit_status(tmp_path)  # noqa: SLF001 - the reader under test
    got = queue_loop._budget_back_off_s(status, _WALL)  # noqa: SLF001 - the clamp under test
    assert got == queue_loop.USAGE_LIMIT_BACKOFF_S


def test_l2_the_driver_names_the_kits_status_file_window_and_codes() -> None:
    """The driver's own copies of the kit's facts, bound to the kit by value.

    The status file's name, the budget window that bounds the back-off, and the
    refusal vocabulary the driver renders - every code the kit can raise.
    """
    source = (ROOT / "ops" / "fleet_kit" / "fleet_headless.py").read_text(encoding="utf-8")
    raised = set(re.findall(r'code="([a-z-]+)"', source))
    raised |= set(re.findall(r'^    code = "([a-z-]+)"$', source, re.MULTILINE))
    facts = {
        "status": kit.STATUS_REL.name == queue_loop.KIT_STATUS_NAME,
        "window": kit.WINDOW_S == queue_loop.KIT_WINDOW_S,
        "codes": raised == set(queue_loop.KIT_REFUSAL_CODES),
    }
    assert all(facts.values()), f"the driver's copy of the kit drifted: {facts}"


def _kit_ending(tmp_path: Path, ending: str) -> tuple[str, int]:
    """What the REAL kit's command line prints, and its exit, for one ending.

    "timeout": the CLI outlives the kit's `--timeout`. "budget-spent": the
    kit's run budget under `tmp_path` already holds its cap of starts.
    "halted": the kit root declares a stop sentinel that stands. "blocked": the
    proxy probe fails, the kit's own `Blocked`. "refused" and "fallback-halted":
    the kit refuses with that code. "limit": the CLI's own fast usage-limit
    refusal, which the kit runs and marks as a limit. The kit's own `main` and
    `spawn` run in this process; nothing live is touched.
    """
    root = tmp_path / "kit-root"
    root.mkdir(parents=True, exist_ok=True)
    if ending == _BUDGET_CODE:
        budget = root / kit.BUDGET_REL
        budget.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now(tz=UTC).timestamp()
        budget.write_bytes(json.dumps({"starts": [now] * kit.RUNS_CAP}).encode("ascii"))
    if ending == "halted":
        hold = root / "ops" / "loop" / "control" / "HOLD_MAIN_SPAWN"
        hold.parent.mkdir(parents=True, exist_ok=True)
        hold.write_bytes(b"synthetic hold\n")
        declared = {"paths": ["ops/loop/control/HOLD_MAIN_SPAWN"]}
        (root / "ops" / "stop_sentinels.json").write_bytes(json.dumps(declared).encode("ascii"))

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if ending == "limit":
            return subprocess.CompletedProcess(argv, 1, json.dumps(_LIMIT_RESULT), "")
        raise subprocess.TimeoutExpired(argv, kwargs.get("timeout") or 0)

    def connect(*_args: Any, **_kwargs: Any) -> _Closable:
        if ending == "blocked":
            raise ConnectionRefusedError
        return _Closable()

    def spawn_fn(root_: Any, code: Any, prompt: Any, **kwargs: Any) -> dict[str, Any]:
        if ending in {"refused", _LIMIT_CODE}:
            raise kit.Refused("synthetic kit refusal", code=ending)
        line: dict[str, Any] = kit.spawn(
            root_,
            code,
            prompt,
            run=fake_run,
            url_source=lambda: "http://127.0.0.1:9",
            connect=connect,
            exe_source=lambda: "synthetic-claude",
            **kwargs,
        )
        return line

    printed = io.StringIO()
    exit_code = kit.main(
        ["spawn", "--root", str(root), "--code", "CS", "--note", "synthetic", "--kind", "build"],
        spawn_fn=spawn_fn,
        stdin=io.StringIO("# synthetic prompt\n"),
        stdout=printed,
    )
    return printed.getvalue().strip(), exit_code


#: The CLI's own fast usage-limit refusal: the refusal's shape, and a message
#: the kit's `classify_limit` reads as a five-hour limit.
_LIMIT_RESULT: Final = {**REFUSAL, "result": "synthetic 5-hour limit reached"}


def _kit_shim(tmp_path: Path, ending: str) -> tuple[Path, int]:
    """A `python` shim that prints the real kit's line for `ending` and exits as it did."""
    line, exit_code = _kit_ending(tmp_path, ending)
    unsafe = sorted(set(line) & _CMD_SPECIALS)
    assert unsafe == [], f"the shim's JSON holds cmd specials {unsafe}"
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir(parents=True, exist_ok=True)
    (shim_dir / "python.cmd").write_bytes(
        b"@echo off\r\necho "
        + line.encode("ascii")
        + b"\r\nexit /b "
        + str(exit_code).encode("ascii")
        + b"\r\n"
    )
    return shim_dir, exit_code


def _ending_runner_log(tmp_path: Path, ending: str) -> tuple[Path, int]:
    """The real runner's log over a shim printing the real kit's line for `ending`."""
    shim_dir, exit_code = _kit_shim(tmp_path, ending)
    return _run_real_runner(tmp_path, shim_dir), exit_code


@pytest.mark.skipif(os.name != "nt", reason="run_lane.ps1 is driven by Windows PowerShell")
@pytest.mark.parametrize(
    ("ending", "kit_exit", "word"),
    [("timeout", 4, "timeout_killed"), (_BUDGET_CODE, 3, "budget_spent")],
    ids=["kit-timeout", "kit-budget-spent"],
)
def test_a_real_runner_log_of_a_kit_ending_is_read_end_to_end(
    tmp_path: Path, ending: str, kit_exit: int, word: str
) -> None:
    """THE RUNNER AND THE DRIVER TOGETHER, over the real kit's printed line.

    The real runner runs over a shim that prints what the REAL kit's command
    line prints for its own timeout and for a spent run budget, and the driver
    reads that very log. Before the repair both read `completed`.
    """
    log, exit_code = _ending_runner_log(tmp_path, ending)
    assert exit_code == kit_exit, f"the in-process kit answered {exit_code}"
    _status(tmp_path / "control", frees_in=60)
    launch, _ = _launches([log, _ok_log(tmp_path / "ok.log")])
    _, rows, _, _, _, _ = _drive(tmp_path, [], budget=1, launch=launch)
    outcome = rows[0]["outcome"]
    assert outcome == word, f"the kit's {ending} ending was recorded as {outcome!r}"


#: Every fast kit ending the adversary measured inside the launcher's grace, and
#: the lane outcome each one must be.
_EARLY_ENDINGS: Final = [
    ("halted", "kit_halted"),
    (_LIMIT_CODE, "usage_refused"),
    ("limit", "usage_refused"),
    ("blocked", "launch_failed"),
    ("refused", "launch_failed"),
    (_BUDGET_CODE, "budget_spent"),
]


@pytest.mark.skipif(os.name != "nt", reason="run_lane.ps1 is driven by Windows PowerShell")
@pytest.mark.parametrize(("ending", "word"), _EARLY_ENDINGS, ids=[e for e, _ in _EARLY_ENDINGS])
def test_r1_a_fast_kit_ending_through_the_real_launcher_and_runner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ending: str, word: str
) -> None:
    """R1, REPRODUCED: the 0.24 s refusal, through the REAL `launch_lane` and runner.

    The launcher's spawn seam runs the REAL `run_lane.ps1` over a shim printing
    what the REAL kit prints for each ending, then raises exactly what
    `_spawn` raises for a runner that exited inside its 2.0 s grace. The real
    `launch_lane` releases, appends its `lane abort` line and re-raises; the
    driver must still read the kit's code off the runner's log. Before the
    repair every one of these read `launch_failed`.
    """
    launcher = queue_loop.lane_launcher
    shim_dir, _kit_exit = _kit_shim(tmp_path, ending)
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(b"# a prompt the shim never reads\n")
    tree = tmp_path / "tree"
    tree.mkdir()
    released: list[Any] = []
    monkeypatch.setattr(launcher, "command_path", lambda _lane, **_kw: prompt)
    monkeypatch.setattr(launcher, "ensure_worktree", lambda _lane, **_kw: tree)
    monkeypatch.setattr(launcher, "_refuse_main_tree", lambda *_args: None)
    monkeypatch.setattr(launcher.lanes, "release_lane", released.append)

    def spawn(runner: Path, prompt_path: Path, cwd: Path, log: Path) -> Any:
        _run_runner_to(runner, prompt_path, cwd, log, shim_dir)
        raise launcher.LaneLaunchError(
            "the runner exited within the grace, so no worker is behind this lane",
            reason=launcher.REASON_RUNNER_EXITED_EARLY,
            waited_s=0.24,
        )

    def launch(lane: str, **kw: Any) -> dict[str, Any]:
        answer: dict[str, Any] = launcher.launch_lane(
            lane, log_dir=tmp_path / "logs", spawn=spawn, **kw
        )
        return answer

    _status(tmp_path / "control", frees_in=600)
    summary, rows, _, _, _, _ = _drive(tmp_path, [], budget=1, launch=launch)
    outcome = rows[0]["outcome"]
    assert outcome == word, f"a fast kit {ending} ending read {outcome!r}"
    assert released == ["T"], "the real launcher did not release the lane on its refusal"
    logs = list((tmp_path / "logs").glob("*.log"))
    aborted = len(logs) == 1 and b"lane abort " in logs[0].read_bytes()
    assert aborted, "the real launcher did not append its abort line to the runner's log"
    assert summary["stopped_by"] != queue_loop.STOPPED_BY_LAUNCH_FAILED
