#!/usr/bin/env python3
r"""The lane runner script, graded by RUNNING it - not by grepping it.

WHY THIS FILE EXISTS SEPARATELY FROM ``tests/test_lane_launcher.py``. That file
states, in its own header, that no arm in it spawns a process, and every arm it
holds about ``ops/loop/run_lane.ps1`` is therefore a text property: the byte
set, the stream folding, the cleared API key. Those arms are worth keeping and
they are all blind to the defect graded here, because the defect is a CONTROL
FLOW one - which lines the script reaches when something upstream of the log
refuses.

THE MEASUREMENT THIS FILE WAS WRITTEN FOR. Thirteen recorded lane cycles left a
worker log holding the "lane start" header line and NOTHING else - no exit line,
no fault, 134 bytes. A log that stops after its header cannot distinguish a
worker that was killed from a worker that crashed from a worker that is still
running, so every one of those cycles was unreadable after the fact. Re-measured
on this machine while diagnosing it: killing a healthy runner two seconds after
its start produces a 134-byte log, byte for byte the same artifact, so the
header-only log is the signature of a DEATH THE SCRIPT NEVER SAW.

AND ONE DEATH IT DOES NOT EVEN GET A HEADER FOR. The command lookup used to run
BEFORE the header was written, so a box with nothing to run produced no log at
all and the launcher recorded ``runner_exited_early`` - a reason word about the
runner, for a fault the runner never had.

CS-1231 SLICE C - THE RUNNER STARTS ITS WORKER THROUGH THE FLEET KIT. FLEET item
10 makes the kit's spawn helper the only path that starts the CLI, so the runner
now runs ``python ops/fleet_kit/fleet_headless.py spawn ...`` and the kit starts
the CLI. Three things follow, and each has an arm here:

- THE COMMAND LINE IS PINNED WHOLE, flag by flag, and today's permission mode is
  carried across rather than widened: the direct start passed
  ``--dangerously-skip-permissions``, which is the CLI's ``bypassPermissions``
  mode, the one value the kit's ``--permission-mode`` pass-through is given.
- THE CONTRACT ARM feeds the command line the runner really produced to the
  REAL ``fleet_headless.main`` in process, so a flag the kit's parser rejects,
  or a value it maps somewhere else, reddens here rather than on a live night.
- THE KIT'S THREE ENDINGS each leave a log the driver can read: exit 0 writes
  the result's text and then the result object whole, so
  ``ops/loop/queue_loop.py`` reads the same tail it always read; exit 3 writes a
  ``lane refused`` line carrying the kit's refusal CODE and never its message;
  exit 4, the kit's timeout, writes the exit line with that code.

THESE ARMS SPAWN A REAL powershell.exe, and that is deliberate: a grep for a
``finally`` block would pass on a script whose ``try`` never encloses the thing
that throws. What is asserted is the FILE ON DISK after a real interpreter has
run the real script.

NO REAL KIT AND NO REAL CLI IS EVER RUN BY THE SCRIPT. ``PATH`` is rebuilt from
a shim directory plus the system directory, so ``python`` resolves to a batch
file this test wrote, or to nothing at all. The batch file hands its argv and
stdin to a recorder script and prints a CANNED kit line - and that line is
produced by the real kit's own ``main`` in this process, over a fake run, so
the shape the runner parses is the shape the kit prints. Nothing reads the
registry, connects, or writes a live budget or status file: the in-process kit
runs against a root under ``tmp_path``. Each runtime arm is FRONTED BY A
CONTROL that asserts the resolution really went the way the arm depends on.

PATHS ARE BOUND TO SCALARS BEFORE THEY ARE ASSERTED ON (CS-850): pytest renders
an asserted expression's sub-expressions with their own reprs whatever message
the assertion carries, and a temporary directory on this platform carries the
account name.
"""

from __future__ import annotations

import ast
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
_TOOLS_DIR: Final = REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from ops.fleet_kit import fleet_headless as kit  # noqa: E402
from toolpath import resolve_tool  # noqa: E402

RUNNER_SOURCE: Final = REPO_ROOT / "ops" / "loop" / "run_lane.ps1"
KIT_SOURCE: Final = REPO_ROOT / "ops" / "fleet_kit" / "fleet_headless.py"
DRIVER_SOURCE: Final = REPO_ROOT / "ops" / "loop" / "queue_loop.py"
STATUS_SOURCE: Final = REPO_ROOT / "ops" / "loop" / "inbox_status.py"

#: The driver's kill budget for one cycle, found by NAME in its source.
CYCLE_BUDGET_NAME: Final = "DEFAULT_CYCLE_TIMEOUT_S"

#: This tree's fleet code, found by NAME in the status module's source.
TREE_CODE_NAME: Final = "CODE"

#: The permission mode the direct start ran under. ``--dangerously-skip-permissions``
#: IS the CLI's bypassPermissions mode; the kit's one pass-through spells it so.
PERMISSION_MODE: Final = "bypassPermissions"

#: What the worker - the CLI behind the kit - exits with. Distinctive, and NOT
#: 0, 1, 3 or 4, so an exit line carrying it cannot have come from a default,
#: a generic failure, or one of the kit's own exit codes.
WORKER_EXIT_CODE: Final = 37

#: Generous, and present only so a wedged arm fails rather than hanging the run.
_CHILD_TIMEOUT_S: Final = 120.0

#: The words that END a lane log. A reader that finds neither is looking at a
#: log whose writer died without saying so, which is the whole defect.
_TERMINAL_PREFIXES: Final = ("lane exit ", "lane fault ", "lane abort ")

#: A SYNTHETIC proxy URL for the in-process kit. Never connected to.
_SYNTHETIC_URL: Final = "http://127.0.0.1:9"

#: Planted in a kit refusal's MESSAGE, which the log must never carry.
_REFUSAL_NEEDLE: Final = "cs1231c-refusal-message-needle"

#: The header's model and effort, read back so the arm follows the config.
_HEADER: Final = re.compile(r" model=(\S+) effort=(\S+) prompt=")

_ON_WINDOWS: Final = pytest.mark.skipif(
    os.name != "nt", reason="run_lane.ps1 is driven by Windows PowerShell"
)


def _powershell() -> str:
    """The interpreter, resolved from PATH and never named as a bare string.

    Returns:
        The absolute path to powershell.exe.
    """
    shell = resolve_tool("powershell")
    if shell is None:
        pytest.skip("powershell could not be resolved from PATH")
    return shell


def _system_dir() -> str:
    """The system directory, which PowerShell needs on PATH to start cleanly.

    Returns:
        The system directory as a string.
    """
    root = os.environ.get("SYSTEMROOT") or r"C:\Windows"
    return str(Path(root) / "System32")


def _env_with_path(shim_dir: Path) -> dict[str, str]:
    """The child's environment with PATH rebuilt from one shim directory.

    The real interpreter is unreachable from here BY CONSTRUCTION rather than
    by an unsetenv that Windows would fold into a differently cased key.

    Args:
        shim_dir: The directory that may or may not hold a ``python`` shim.

    Returns:
        The environment to hand the child.
    """
    env = {key: value for key, value in os.environ.items() if key.upper() != "PATH"}
    env["PATH"] = f"{shim_dir}{os.pathsep}{_system_dir()}"
    # The runner clears this for its own process; cleared here too so that a
    # machine-scope key can never make an arm depend on a credit balance.
    env.pop("ANTHROPIC_API_KEY", None)
    # CS-1225 - the runner refuses an ANTHROPIC_BASE_URL outside the loopback
    # allowlist before it looks anything up. A SYNTHETIC value in that shape,
    # so no arm depends on this machine's route; the shim never connects.
    env["ANTHROPIC_BASE_URL"] = "http://localhost:3456/synthetic/route"
    return env


def _resolves_python(shim_dir: Path) -> bool:
    """Whether ``python`` resolves at all under this arm's PATH.

    THE CONTROL for every runtime arm. A runner that wrote an exit line because
    it skipped its whole body looks identical to one that wrote it because the
    body ran, and only this probe separates them.

    Args:
        shim_dir: The directory to put first on PATH.

    Returns:
        True when Get-Command finds something.
    """
    done = subprocess.run(
        [
            _powershell(),
            "-NoProfile",
            "-Command",
            "if (Get-Command python -ErrorAction SilentlyContinue) { 'FOUND' } else { 'MISSING' }",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=_CHILD_TIMEOUT_S,
        env=_env_with_path(shim_dir),
    )
    return done.stdout.strip() == "FOUND"


class _Closable:
    """What the fake connect hands back: something the kit can close."""

    def close(self) -> None:
        """Nothing to close."""


def _connect(_address: object, timeout: float = 0.0) -> _Closable:
    """The kit's liveness probe, answered without a socket."""
    del timeout
    return _Closable()


def _kit_print(
    tmp_path: Path,
    *,
    receipt: dict[str, Any] | None = None,
    rc: int = 0,
    refusal_code: str | None = None,
    timed_out: bool = False,
) -> tuple[str, int]:
    """What the REAL kit's command line prints, and its exit code, for one ending.

    The kit's own ``main`` runs in this process against a root under
    ``tmp_path``; the CLI is a fake ``run`` and the proxy URL, the connect and
    the executable are injected, so nothing live is read or written.

    Args:
        tmp_path: The test's scratch directory.
        receipt: The CLI's JSON result object, for a run that ended.
        rc: The CLI's exit code, for a run that ended.
        refusal_code: When set, the kit refuses with this code.
        timed_out: When True, the run times out.

    Returns:
        The one line the kit printed, and the kit's exit code.
    """
    root = tmp_path / "kit-root"
    root.mkdir(parents=True, exist_ok=True)

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if timed_out:
            raise subprocess.TimeoutExpired(argv, kwargs.get("timeout") or 0)
        return subprocess.CompletedProcess(argv, rc, json.dumps(receipt), "")

    def spawn_fn(root: Any, code: Any, prompt: Any, **kwargs: Any) -> dict[str, Any]:
        if refusal_code is not None:
            raise kit.Refused(f"synthetic refusal {_REFUSAL_NEEDLE}", code=refusal_code)
        line: dict[str, Any] = kit.spawn(
            root,
            code,
            prompt,
            run=fake_run,
            url_source=lambda: _SYNTHETIC_URL,
            connect=_connect,
            exe_source=lambda: "synthetic-claude",
            **kwargs,
        )
        return line

    printed = io.StringIO()
    code = kit.main(
        ["spawn", "--root", str(root), "--code", "CS", "--note", "synthetic", "--kind", "build"],
        spawn_fn=spawn_fn,
        stdin=io.StringIO("# synthetic prompt\n"),
        stdout=printed,
    )
    return printed.getvalue().strip(), code


#: The recorder the shim hands its argv and stdin to. It writes both beside
#: itself and prints the canned kit line, exiting with the canned code.
_RECORDER: Final = (
    "import json, sys\n"
    "from pathlib import Path\n"
    "here = Path(__file__).resolve().parent\n"
    "(here / 'argv.json').write_text(json.dumps(sys.argv[1:]), encoding='utf-8')\n"
    "(here / 'stdin.bin').write_bytes(sys.stdin.buffer.read())\n"
    "sys.stdout.write((here / 'canned.txt').read_text(encoding='ascii') + '\\n')\n"
    "sys.stdout.flush()\n"
    "sys.exit(int((here / 'exit.txt').read_text(encoding='ascii')))\n"
)


def _shim(tmp_path: Path, line: str, exit_code: int) -> Path:
    """A directory holding a ``python`` that records and prints one kit line.

    The shim calls THIS interpreter by its absolute path, so the recorder runs
    whatever PATH the runner was handed; the path lives only under tmp_path.

    Args:
        tmp_path: The test's scratch directory.
        line: The kit line the shim prints.
        exit_code: What the shim exits with.

    Returns:
        The shim directory.
    """
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir(parents=True, exist_ok=True)
    (shim_dir / "recorder.py").write_bytes(_RECORDER.encode("ascii"))
    (shim_dir / "canned.txt").write_bytes(line.encode("ascii"))
    (shim_dir / "exit.txt").write_bytes(str(exit_code).encode("ascii"))
    (shim_dir / "python.cmd").write_bytes(
        b"@echo off\r\n"
        + b'"'
        + sys.executable.encode("mbcs" if os.name == "nt" else "utf-8")
        + b'" "%~dp0recorder.py" %*\r\n'
        + b"exit /b %ERRORLEVEL%\r\n"
    )
    return shim_dir


def _recorded(shim_dir: Path) -> tuple[list[str], bytes] | None:
    """The argv and stdin the shim was handed, or None when it never ran.

    Args:
        shim_dir: The shim directory.

    Returns:
        The argv (without the recorder) and the raw stdin bytes.
    """
    argv_file = shim_dir / "argv.json"
    if not argv_file.is_file():
        return None
    argv = json.loads(argv_file.read_text(encoding="utf-8"))
    return argv, (shim_dir / "stdin.bin").read_bytes()


def _empty(tmp_path: Path) -> Path:
    """A directory holding no ``python`` at all - and a DECOY ``claude``.

    The decoy is what makes the arms below discriminate: a runner that still
    started the CLI directly would find it and run it, leaving its marker, and
    would never fault on a missing interpreter.

    Args:
        tmp_path: The test's scratch directory.

    Returns:
        The directory.
    """
    empty = tmp_path / "no-python"
    empty.mkdir(exist_ok=True)
    (empty / "claude.cmd").write_bytes(b'@echo decoy> "%~dp0decoy.txt"\r\n@exit /b 0\r\n')
    return empty


def _decoy_ran(empty: Path) -> bool:
    """Whether the runner started the decoy CLI directly."""
    return (empty / "decoy.txt").is_file()


_PROMPT_TEXT: Final = "# a prompt the recorder keeps\n"


def _run_runner(tmp_path: Path, shim_dir: Path) -> tuple[Path, subprocess.CompletedProcess[str]]:
    """Run the real runner against planted paths and hand back its log.

    Args:
        tmp_path: The test's scratch directory.
        shim_dir: The directory placed first on the child's PATH.

    Returns:
        The log path and the completed process.
    """
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(_PROMPT_TEXT.encode("ascii"))
    cwd = tmp_path / "tree"
    cwd.mkdir(exist_ok=True)
    log = tmp_path / "lane_queue_synthetic.log"
    done = subprocess.run(
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
            str(cwd),
            "-Log",
            str(log),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=_CHILD_TIMEOUT_S,
        env=_env_with_path(shim_dir),
    )
    return log, done


def _log_lines(log: Path) -> list[str]:
    """The log's non-empty lines, decoded tolerantly of the BOM Out-File writes.

    Args:
        log: The log file.

    Returns:
        The non-empty lines.
    """
    if not log.is_file():
        return []
    text = log.read_bytes().decode("utf-8-sig", errors="replace")
    return [line.strip() for line in text.splitlines() if line.strip()]


def _json_lines(lines: list[str]) -> list[Any]:
    """Every line of the log that parses as JSON, in order."""
    found: list[Any] = []
    for line in lines:
        if not line.startswith("{"):
            continue
        try:
            found.append(json.loads(line))
        except ValueError:
            continue
    return found


def _module_constant(source: Path, name: str) -> object:
    """A module-level literal, found by name in Python source, else None.

    Args:
        source: The module's file.
        name: The constant's name.

    Returns:
        The literal's value when exactly one top-level assignment binds it.
    """
    values: list[object] = []
    for node in ast.parse(source.read_text(encoding="utf-8")).body:
        target: ast.expr | None = None
        value: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign):
            target, value = node.target, node.value
        if isinstance(target, ast.Name) and target.id == name:
            values.append(value.value if isinstance(value, ast.Constant) else None)
    return values[0] if len(values) == 1 else None


def _norm(item: str) -> str:
    """One argv item, a path normalised so two spellings of it compare equal."""
    if Path(item).is_absolute():
        return os.path.normcase(os.path.realpath(item))
    return item


def _redacted(argv: list[str]) -> list[str]:
    """The argv with every absolute path replaced, safe to render (CS-850)."""
    return ["<path>" if Path(item).is_absolute() else item for item in argv]


# ===========================================================================
# a. A worker that runs - the control for everything below
# ===========================================================================

#: The CLI's result for a run that did its work.
_RECEIPT: Final = {
    "type": "result",
    "subtype": "success",
    "is_error": False,
    "num_turns": 3,
    "total_cost_usd": 0.5,
    "result": "the shim ran",
}


@_ON_WINDOWS
def test_a_runner_whose_worker_exits_records_the_header_the_output_and_the_code(
    tmp_path: Path,
) -> None:
    """The control - a complete log is reachable, so a truncated one is a defect.

    A log that stops after its header is only a fault if a full one can be
    written at all, and this is the arm that shows one can.

    All three parts are asserted, because any one alone is satisfied by a
    runner that wrote a constant: the header names the cwd it was given, the
    body carries the worker's own words, and the exit line carries the
    WORKER's own exit code - the CLI's, carried in the kit line's ``rc``, not
    the kit's own 0.
    """
    line, kit_code = _kit_print(tmp_path, receipt=_RECEIPT, rc=WORKER_EXIT_CODE)
    assert kit_code == kit.CLI_OK
    shim_dir = _shim(tmp_path, line, kit_code)
    resolves = _resolves_python(shim_dir)
    assert resolves, "the shim did not reach PATH - the arm grades nothing"

    log, done = _run_runner(tmp_path, shim_dir)
    ran = done.returncode
    assert ran == 0, f"the runner itself failed - stderr was {done.stderr[:400]!r}"

    lines = _log_lines(log)
    assert lines, "the runner wrote no log at all"

    started = lines[0].startswith("lane start ")
    assert started, f"the first line is not a start header: {lines[0][:80]!r}"

    carried = "the shim ran" in lines
    assert carried, "the worker's own words never reached the log as a readable line"

    ended = lines[-1]
    assert ended.startswith("lane exit "), f"the last line is not an exit line: {ended[:80]!r}"

    coded = ended.endswith(f"code={WORKER_EXIT_CODE}")
    assert coded, f"the exit line does not carry the worker's code: {ended[:80]!r}"


@_ON_WINDOWS
def test_the_result_object_is_written_whole_after_its_text(tmp_path: Path) -> None:
    """The driver reads the LAST result object off the log's tail - CS-1178.

    The kit prints its usage line with the CLI's result nested under
    ``receipt``; the runner writes the result's text as readable lines, then
    the result object whole on one line, so ``_worker_result`` in
    ``ops/loop/queue_loop.py`` reads it exactly as it did off the direct start.
    The kit's own usage line is NOT the last JSON line: it is not a result
    object, and its nested copy would double the tail the driver reads.
    """
    line, kit_code = _kit_print(tmp_path, receipt=_RECEIPT, rc=0)
    shim_dir = _shim(tmp_path, line, kit_code)
    resolves = _resolves_python(shim_dir)
    assert resolves, "the shim did not reach PATH - the arm grades nothing"

    log, _done = _run_runner(tmp_path, shim_dir)
    lines = _log_lines(log)
    objects = _json_lines(lines)
    assert objects, "no JSON line reached the log"
    whole = objects[-1] == _RECEIPT
    assert whole, "the last JSON line is not the CLI's result object, whole"
    nested = [obj for obj in objects if isinstance(obj, dict) and "receipt" in obj]
    assert nested == [], "the kit's usage line was written into the log"
    text_at = lines.index("the shim ran") if "the shim ran" in lines else -1
    object_at = max(i for i, item in enumerate(lines) if item.startswith("{"))
    ordered = 0 <= text_at < object_at
    assert ordered, "the result's text does not precede the result object"


# ===========================================================================
# b. The command line - pinned whole, and accepted by the real kit
# ===========================================================================


def _expected_argv(tmp_path: Path, model: str, effort: str) -> list[str]:
    """The kit command line the runner must produce, flag by flag.

    Args:
        tmp_path: The test's scratch directory, holding the cwd and the log.
        model: The model the runner's header recorded.
        effort: The effort the runner's header recorded.

    Returns:
        The argv after the interpreter.
    """
    cycle = _module_constant(DRIVER_SOURCE, CYCLE_BUDGET_NAME)
    code = _module_constant(STATUS_SOURCE, TREE_CODE_NAME)
    return [
        str(KIT_SOURCE),
        "spawn",
        "--root",
        str(REPO_ROOT),
        "--code",
        str(code),
        "--note",
        "lane_queue_synthetic",
        "--kind",
        "build",
        "--writes-code",
        "--model",
        model,
        "--effort",
        effort,
        "--floors-in-hooks",
        "--permission-mode",
        PERMISSION_MODE,
        "--timeout",
        str(cycle),
        "--cwd",
        str(tmp_path / "tree"),
    ]


def _recorded_run(tmp_path: Path) -> tuple[list[str], bytes, list[str]]:
    """Run the runner over a recording shim; hand back argv, stdin and log lines."""
    line, kit_code = _kit_print(tmp_path, receipt=_RECEIPT, rc=0)
    shim_dir = _shim(tmp_path, line, kit_code)
    resolves = _resolves_python(shim_dir)
    assert resolves, "the shim did not reach PATH - the arm grades nothing"
    log, _done = _run_runner(tmp_path, shim_dir)
    seen = _recorded(shim_dir)
    assert seen is not None, "the shim never ran - the arm grades nothing"
    argv, stdin = seen
    return argv, stdin, _log_lines(log)


@_ON_WINDOWS
def test_the_runner_starts_its_worker_through_the_kits_spawn_command_line(
    tmp_path: Path,
) -> None:
    """FLEET item 10: the kit starts the CLI; the runner only starts the kit.

    The whole command line is pinned. The permission mode is today's - the
    direct start's ``--dangerously-skip-permissions`` is the CLI's
    ``bypassPermissions`` mode - and the timeout is the driver's own cycle
    budget, so the kit's one-hour default never kills a worker the driver
    would still have waited for.
    """
    argv, _stdin, lines = _recorded_run(tmp_path)
    header = _HEADER.search(lines[0]) if lines else None
    assert header is not None, "the header does not name the model and effort"
    expected = _expected_argv(tmp_path, header.group(1), header.group(2))
    same = [_norm(item) for item in argv] == [_norm(item) for item in expected]
    assert same, f"the kit command line differs: {_redacted(argv)} != {_redacted(expected)}"


@_ON_WINDOWS
def test_the_runner_pipes_the_prompt_to_the_kit_on_stdin(tmp_path: Path) -> None:
    """The prompt still travels on stdin - no quoting risk, no length ceiling."""
    argv, stdin, _lines = _recorded_run(tmp_path)
    piped = _PROMPT_TEXT.strip().encode("ascii") in stdin
    assert piped, "the prompt did not reach the kit on stdin"
    no_file_flag = "--prompt-file" not in argv
    assert no_file_flag, "the prompt is passed twice"


@_ON_WINDOWS
def test_the_recorded_command_line_is_one_the_real_kit_accepts(tmp_path: Path) -> None:
    """THE CONTRACT ARM: the runner's real argv, fed to the real kit's ``main``.

    ``spawn_fn`` records what ``main`` mapped the flags to, then runs the REAL
    ``spawn`` against a root under ``tmp_path`` with a fake CLI, so the CLI
    argv the kit would start is graded too: the permission mode arrives as the
    kit's one pass-through and nothing wider, the CLI is asked for its JSON
    result, the floors stay in hooks, and the result lands under ``receipt`` in
    the printed line - where the runner reads it.
    """
    argv, stdin, _lines = _recorded_run(tmp_path)
    kit_path = _norm(argv[0]) == _norm(str(KIT_SOURCE))
    assert kit_path, "the runner did not run the vendored kit"

    mapped: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    started: list[list[str]] = []

    def fake_run(cli_argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        started.append(list(cli_argv))
        return subprocess.CompletedProcess(cli_argv, 0, json.dumps(_RECEIPT), "")

    def recorder(root: Any, code: Any, prompt: Any, **kwargs: Any) -> dict[str, Any]:
        mapped.append(((root, code, prompt), dict(kwargs)))
        line: dict[str, Any] = kit.spawn(
            tmp_path / "contract-root",
            code,
            prompt,
            run=fake_run,
            url_source=lambda: _SYNTHETIC_URL,
            connect=_connect,
            exe_source=lambda: "synthetic-claude",
            **kwargs,
        )
        return line

    printed = io.StringIO()
    code = kit.main(
        argv[1:],
        spawn_fn=recorder,
        stdin=io.StringIO(stdin.decode("ascii", errors="replace")),
        stdout=printed,
    )
    assert code == kit.CLI_OK, f"the kit's command line answered {code}"
    assert len(mapped) == 1, "the kit did not map the command line to one spawn"
    args, kwargs = mapped[0]
    root_is_repo = _norm(str(args[0])) == _norm(str(REPO_ROOT))
    cwd_is_tree = _norm(str(kwargs.get("cwd"))) == _norm(str(tmp_path / "tree"))
    facts = {
        "root": root_is_repo,
        "cwd": cwd_is_tree,
        "extra": kwargs.get("extra") == ("--permission-mode", PERMISSION_MODE),
        "floors_in_hooks": kwargs.get("floors_in_hooks") is True,
        "writes_code": kwargs.get("writes_code") is True,
        "kind": kwargs.get("kind") == "build",
        "timeout": kwargs.get("timeout") == _module_constant(DRIVER_SOURCE, CYCLE_BUDGET_NAME),
        "prompt": _PROMPT_TEXT.strip() in str(args[2]),
    }
    assert all(facts.values()), f"the kit mapped the command line otherwise: {facts}"

    assert len(started) == 1, "the kit did not start exactly one CLI"
    cli = started[0]
    cli_facts = {
        "json": cli[cli.index("--output-format") + 1] == "json",
        "mode": cli[-2:] == ["--permission-mode", PERMISSION_MODE],
        "no_skip_flag": "--dangerously-skip-permissions" not in cli,
        "no_bare": "--bare" not in cli,
        "no_fallback": not any("fallback" in item for item in cli),
    }
    assert all(cli_facts.values()), f"the CLI argv the kit built is not today's: {cli_facts}"

    line = json.loads(printed.getvalue())
    landed = line.get("receipt") == _RECEIPT and line.get("result") == _RECEIPT["result"]
    assert landed, "the result does not sit under receipt in the kit's printed line"


def test_the_permission_mode_the_runner_passes_is_one_the_kit_allows() -> None:
    """STATIC, so it runs everywhere: the runner's literal is in the kit's set."""
    text = RUNNER_SOURCE.read_bytes().decode("ascii")
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    passed = re.findall(r'"--permission-mode",\s*"([A-Za-z]+)"', code)
    assert passed == [PERMISSION_MODE]
    assert PERMISSION_MODE in kit.PERMISSION_MODES


def test_the_kit_timeout_the_runner_passes_is_the_drivers_cycle_budget() -> None:
    """STATIC: the kit's ceiling never undercuts the driver's own kill.

    The direct start had no ceiling of its own; the driver killed the tree at
    its cycle budget. The kit defaults to one hour, so the runner hands it the
    driver's budget, found here by NAME in the driver's source.
    """
    text = RUNNER_SOURCE.read_bytes().decode("ascii")
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    passed = re.findall(r'"--timeout",\s*"([0-9]+)"', code)
    budget = _module_constant(DRIVER_SOURCE, CYCLE_BUDGET_NAME)
    assert isinstance(budget, int)
    assert passed == [str(budget)]


# ===========================================================================
# c. The kit's other two endings - refused, and timed out
# ===========================================================================


@_ON_WINDOWS
def test_a_kit_refusal_writes_its_code_and_never_its_message(tmp_path: Path) -> None:
    """Exit 3: a ``lane refused`` line naming the kit's CODE, then the exit line.

    The code is a fixed kit vocabulary word. The message is not written: it is
    free text built from an exception, and this log is written unattended
    (CLAUDE.md non-negotiable 12).
    """
    line, kit_code = _kit_print(tmp_path, refusal_code="budget-spent")
    assert kit_code == kit.CLI_REFUSED
    shim_dir = _shim(tmp_path, line, kit_code)
    resolves = _resolves_python(shim_dir)
    assert resolves, "the shim did not reach PATH - the arm grades nothing"

    log, done = _run_runner(tmp_path, shim_dir)
    lines = _log_lines(log)
    refused = [item for item in lines if item.startswith("lane refused ")]
    named = len(refused) == 1 and refused[0].endswith(" kit_code=budget-spent")
    assert named, f"no lane refused line names the kit's code: {refused}"
    leaked = any(_REFUSAL_NEEDLE in item for item in lines)
    assert leaked is False, "the kit's refusal message reached the log"
    ended = lines[-1] if lines else ""
    exited = ended.startswith("lane exit ")
    assert exited, f"the last line is not an exit line: {ended[:80]!r}"
    coded = ended.endswith(f"code={kit.CLI_REFUSED}")
    assert coded, f"the exit line does not carry the refusal code: {ended[:80]!r}"
    assert done.returncode == kit.CLI_REFUSED


@_ON_WINDOWS
def test_a_refusal_code_outside_the_plain_vocabulary_is_never_echoed(tmp_path: Path) -> None:
    """A code that is not a plain lower-case word is written as ``unknown``.

    The sibling of the arm above: the runner trusts no field of the kit's line
    to be path-free, so a code shaped like anything else never reaches the log.
    """
    line, kit_code = _kit_print(tmp_path, refusal_code="C:" + "\\" + _REFUSAL_NEEDLE)
    shim_dir = _shim(tmp_path, line, kit_code)
    resolves = _resolves_python(shim_dir)
    assert resolves, "the shim did not reach PATH - the arm grades nothing"

    log, _done = _run_runner(tmp_path, shim_dir)
    lines = _log_lines(log)
    leaked = any(_REFUSAL_NEEDLE in item for item in lines)
    assert leaked is False, "a refusal code outside the vocabulary reached the log"
    unknown = any(
        item.startswith("lane refused ") and item.endswith(" kit_code=unknown") for item in lines
    )
    assert unknown, "the refusal was not recorded as unknown"


@_ON_WINDOWS
def test_a_kit_timeout_ends_on_the_kits_timeout_code(tmp_path: Path) -> None:
    """Exit 4: the kit killed the tree at its ceiling; the log says so by code."""
    line, kit_code = _kit_print(tmp_path, timed_out=True)
    assert kit_code == kit.CLI_TIMEOUT
    shim_dir = _shim(tmp_path, line, kit_code)
    resolves = _resolves_python(shim_dir)
    assert resolves, "the shim did not reach PATH - the arm grades nothing"

    log, _done = _run_runner(tmp_path, shim_dir)
    lines = _log_lines(log)
    ended = lines[-1] if lines else ""
    coded = ended.startswith("lane exit ") and ended.endswith(f"code={kit.CLI_TIMEOUT}")
    assert coded, f"the exit line does not carry the kit's timeout code: {ended[:80]!r}"
    refused = any(item.startswith(("lane refused ", "lane fault ")) for item in lines)
    assert refused is False


# ===========================================================================
# d. A worker that cannot start - the 134-byte log
# ===========================================================================


@_ON_WINDOWS
def test_a_runner_that_cannot_resolve_the_interpreter_still_writes_a_header(
    tmp_path: Path,
) -> None:
    """A log that does not exist is worse than one that stops after its header.

    ``Get-Command python -ErrorAction Stop`` is a TERMINATING failure. Run
    before the header, it would end the script with nothing on disk, and the
    launcher's liveness grace would then record ``runner_exited_early`` - a
    reason word about the runner for a fault the runner never had.
    """
    empty = _empty(tmp_path)
    missing = not _resolves_python(empty)
    assert missing, "python is still on PATH - the arm grades nothing"

    log, _done = _run_runner(tmp_path, empty)
    wrote = log.is_file()
    assert wrote, "the runner died without writing a log at all"

    lines = _log_lines(log)
    started = bool(lines) and lines[0].startswith("lane start ")
    assert started, "the log does not open with a start header"


@_ON_WINDOWS
def test_a_runner_that_cannot_resolve_the_interpreter_still_records_a_terminal_line(
    tmp_path: Path,
) -> None:
    """THE DEFECT ITSELF. Thirteen recorded cycles ended here.

    Whatever refuses, the runner must say that it stopped. A log whose last line
    is the header cannot be told apart from a worker still running, and that is
    what made every failing cycle on both recorded nights unreadable.
    """
    empty = _empty(tmp_path)
    missing = not _resolves_python(empty)
    assert missing, "python is still on PATH - the arm grades nothing"

    log, _done = _run_runner(tmp_path, empty)
    lines = _log_lines(log)
    assert lines, "the runner wrote no log at all"

    ended = lines[-1]
    terminal = ended.startswith(_TERMINAL_PREFIXES)
    assert terminal, f"the log stops without a terminal line: {ended[:120]!r}"


@_ON_WINDOWS
def test_a_runner_that_cannot_resolve_the_interpreter_names_the_fault_symbolically(
    tmp_path: Path,
) -> None:
    """A terminal line that says nothing about WHY is half a diagnosis.

    The fault is named by its exception TYPE and its FullyQualifiedErrorId,
    never by ``$_.Exception.Message``. That is the same rule the Python half
    obeys: an error id is symbolic and path-free by construction, while a
    message routinely embeds the path it failed on (CLAUDE.md non-negotiable
    12), and this log is written by an unattended process nobody is watching.
    """
    empty = _empty(tmp_path)
    missing = not _resolves_python(empty)
    assert missing, "python is still on PATH - the arm grades nothing"

    log, _done = _run_runner(tmp_path, empty)
    direct = _decoy_ran(empty)
    assert direct is False, "the runner started the CLI directly, past the kit"
    lines = _log_lines(log)
    faults = [line for line in lines if line.startswith("lane fault ")]
    assert faults, "nothing in the log names the fault"

    named = "CommandNotFoundException" in faults[0]
    assert named, f"the fault line does not name the refusal: {faults[0][:120]!r}"
