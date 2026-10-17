"""CS-1225 - every headless spawn is routed through the local proxy, or refused.

The arms below grade `ops/loop/headless_route.py`: the child environment it
builds, the two refusals (an unset variable, a proxy nobody is listening on),
the user-store-first read order, and the exit classifier a caller backs off on.

NO ARM READS THE REAL USER STORE OR TOUCHES THE REAL PROXY PORT. Every call
injects the store reader, and every connect goes to an EPHEMERAL loopback port
this module opened (or opened and closed) itself. No arm spawns a process.

NO ARM RENDERS A URL VALUE (CLAUDE.md rules 12 and 13). Every comparison
against a planted value is bound to a bool first, because pytest renders the
sub-expressions of an asserted comparison whatever message it carries.
"""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.fleet_kit import fleet_headless as kit  # noqa: E402
from ops.fleet_kit import fleet_subagent_first as subagent_first  # noqa: E402
from ops.loop import headless_route  # noqa: E402

#: The source variable, spelled once here so a rename reddens every arm.
SOURCE: Final = "CLAUDE_HEADLESS_BASE_URL"
#: The variable the child CLI reads.
TARGET: Final = "ANTHROPIC_BASE_URL"


def _store(value: str | None) -> Callable[[str], str | None]:
    """A user-store reader that answers ``value`` for the source name only."""

    def read(name: str) -> str | None:
        return value if name == SOURCE else None

    return read


@pytest.fixture
def listening() -> Iterator[int]:
    """An ephemeral loopback port with a live listener behind it."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(4)
    try:
        yield int(server.getsockname()[1])
    finally:
        server.close()


@pytest.fixture
def dead_port() -> int:
    """An ephemeral loopback port that was bound, then released - nobody listens."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = int(probe.getsockname()[1])
    probe.close()
    return port


def _url(port: int) -> str:
    return f"http://127.0.0.1:{port}"


def test_the_route_constants_are_the_ruled_ones() -> None:
    """The probe target is the ruled loopback proxy, and the names are the ruled ones."""
    assert headless_route.SOURCE_VAR == SOURCE
    assert headless_route.TARGET_VAR == TARGET
    assert headless_route.PROXY_PORT == 3456  # noqa: PLR2004 - the ruled port
    assert 0 < headless_route.CONNECT_TIMEOUT_S <= 2.0  # noqa: PLR2004 - ruled ceiling


def test_an_unset_variable_refuses(monkeypatch: pytest.MonkeyPatch, listening: int) -> None:
    """Neither store holds the variable: refused, naming the variable."""
    monkeypatch.delenv(SOURCE, raising=False)
    with pytest.raises(headless_route.HeadlessRouteRefused) as caught:
        headless_route.child_env({}, port=listening, user_store=_store(None))
    reason = caught.value.reason
    assert SOURCE in reason
    assert reason == headless_route.REASON_UNSET


def test_an_empty_variable_refuses(monkeypatch: pytest.MonkeyPatch, listening: int) -> None:
    """A blank value is not a route."""
    monkeypatch.setenv(SOURCE, "   ")
    with pytest.raises(headless_route.HeadlessRouteRefused) as caught:
        headless_route.child_env({}, port=listening, user_store=_store(""))
    assert caught.value.reason == headless_route.REASON_UNSET


def test_a_refused_port_refuses(monkeypatch: pytest.MonkeyPatch, dead_port: int) -> None:
    """The variable is set but nothing listens: refused, no fallback."""
    monkeypatch.delenv(SOURCE, raising=False)
    with pytest.raises(headless_route.HeadlessRouteRefused) as caught:
        headless_route.child_env({}, port=dead_port, user_store=_store(_url(dead_port)))
    assert caught.value.reason == headless_route.REASON_PROXY_DOWN


def test_a_connect_timeout_refuses(monkeypatch: pytest.MonkeyPatch, listening: int) -> None:
    """A connect that times out is a refusal, the same as one refused outright."""
    monkeypatch.delenv(SOURCE, raising=False)
    seen: list[float] = []

    def timing_out(address: tuple[str, int], timeout: float) -> socket.socket:
        del address
        seen.append(timeout)
        raise TimeoutError

    with pytest.raises(headless_route.HeadlessRouteRefused) as caught:
        headless_route.child_env(
            {}, port=listening, user_store=_store(_url(listening)), connect=timing_out
        )
    assert caught.value.reason == headless_route.REASON_PROXY_DOWN
    assert seen == [headless_route.CONNECT_TIMEOUT_S]


def test_a_value_naming_another_host_refuses(
    monkeypatch: pytest.MonkeyPatch, listening: int
) -> None:
    """A value that does not name the probed loopback proxy is not routed."""
    monkeypatch.delenv(SOURCE, raising=False)
    planted = f"http://192.0.2.1:{listening}"
    with pytest.raises(headless_route.HeadlessRouteRefused) as caught:
        headless_route.child_env({}, port=listening, user_store=_store(planted))
    assert caught.value.reason == headless_route.REASON_NOT_LOCAL


def test_a_set_variable_and_a_live_port_route_the_child(
    monkeypatch: pytest.MonkeyPatch, listening: int
) -> None:
    """The happy path: the key is set on a COPY, and os.environ is untouched."""
    monkeypatch.delenv(SOURCE, raising=False)
    monkeypatch.delenv(TARGET, raising=False)
    before = dict(os.environ)
    base = {"PATH": "planted-path", "ANTHROPIC_API_KEY": "planted-key"}
    planted = _url(listening)
    env = headless_route.child_env(base, port=listening, user_store=_store(planted))
    routed = env.get(TARGET) == planted
    copied = env is not base
    base_untouched = base == {"PATH": "planted-path", "ANTHROPIC_API_KEY": "planted-key"}
    environ_untouched = dict(os.environ) == before
    key_dropped = "ANTHROPIC_API_KEY" not in env
    path_kept = env.get("PATH") == "planted-path"
    assert (routed, copied, base_untouched, environ_untouched, key_dropped, path_kept) == (
        True,
    ) * 6


def test_the_user_store_wins_over_the_process_env(
    monkeypatch: pytest.MonkeyPatch, listening: int
) -> None:
    """Registry first: a stale process copy never outranks the user store."""
    from_store = _url(listening)
    monkeypatch.setenv(SOURCE, f"http://127.0.0.1:{listening}/stale")
    env = headless_route.child_env({}, port=listening, user_store=_store(from_store))
    store_won = env.get(TARGET) == from_store
    assert store_won


def _unreadable_store(name: str) -> str | None:
    """A user store that cannot be read at all."""
    del name
    raise headless_route.UserStoreUnreadableError


def test_the_process_env_is_read_only_when_the_store_is_unreadable(
    monkeypatch: pytest.MonkeyPatch, listening: int
) -> None:
    """No readable store (off Windows, key unopenable): the process copy is read."""
    planted = _url(listening)
    monkeypatch.setenv(SOURCE, planted)
    env = headless_route.child_env({}, port=listening, user_store=_unreadable_store)
    fell_back = env.get(TARGET) == planted
    assert fell_back


def test_an_absent_store_value_refuses_despite_an_inherited_copy(
    monkeypatch: pytest.MonkeyPatch, listening: int
) -> None:
    """THE KILL SWITCH: deleting the user variable stops the spawn, inherited copy or not."""
    monkeypatch.setenv(SOURCE, _url(listening))
    with pytest.raises(headless_route.HeadlessRouteRefused) as caught:
        headless_route.child_env({}, port=listening, user_store=_store(None))
    assert caught.value.reason == headless_route.REASON_UNSET


def test_an_unreadable_store_and_no_process_copy_refuses(
    monkeypatch: pytest.MonkeyPatch, listening: int
) -> None:
    monkeypatch.delenv(SOURCE, raising=False)
    with pytest.raises(headless_route.HeadlessRouteRefused) as caught:
        headless_route.child_env({}, port=listening, user_store=_unreadable_store)
    assert caught.value.reason == headless_route.REASON_UNSET


_BACKSLASH: Final = chr(92)


@pytest.mark.parametrize(
    "planted",
    [
        "http://evil.example" + _BACKSLASH + "@127.0.0.1:{port}",
        "http://user:pw@127.0.0.1:{port}",
        "http://evil.example@127.0.0.1:{port}",
        "http://127.0.0.1:{port}/a?x=1",
        "http://127.0.0.1:{port}/a#frag",
        "http://127.0.0.1:{port}/a b",
        " http://127.0.0.1:{port}",
        "http://127.0.0.1:{port}\n",
        "http://127.0.0.1:{port}" + _BACKSLASH + "a",
        "http://127.0.0.2:{port}",
        "http://127.0.0.1:{port}0",
        "ftp://127.0.0.1:{port}",
        "http://localhost.evil.example:{port}",
    ],
    ids=[
        "backslash-at",
        "userinfo",
        "at-host",
        "query",
        "fragment",
        "inner-space",
        "leading-space",
        "trailing-newline",
        "backslash-path",
        "other-loopback",
        "longer-port",
        "scheme",
        "suffix-host",
    ],
)
def test_a_value_outside_the_allowlist_refuses(
    monkeypatch: pytest.MonkeyPatch, listening: int, planted: str
) -> None:
    """Whole-string allowlist: every parser-confusion shape is refused before any connect."""
    monkeypatch.delenv(SOURCE, raising=False)
    connects: list[object] = []

    def recording(address: tuple[str, int], timeout: float) -> socket.socket:
        connects.append((address, timeout))
        raise ConnectionRefusedError

    with pytest.raises(headless_route.HeadlessRouteRefused) as caught:
        headless_route.child_env(
            {},
            port=listening,
            user_store=_store(planted.format(port=listening)),
            connect=recording,
        )
    reason = caught.value.reason
    assert (reason == headless_route.REASON_NOT_LOCAL, len(connects)) == (True, 0)


@pytest.mark.parametrize(
    "shape",
    [
        "http://localhost:{port}/abcdefghijklmnop/qrstuvwxyz0123",
        "http://localhost:{port}/seg-one/seg_two/",
        "http://127.0.0.1:{port}",
        "https://localhost:{port}",
    ],
)
def test_a_loopback_value_with_url_safe_segments_is_accepted(
    monkeypatch: pytest.MonkeyPatch, listening: int, shape: str
) -> None:
    """The real value's shape - http, localhost, the port, two URL-safe segments - routes."""
    monkeypatch.delenv(SOURCE, raising=False)
    planted = shape.format(port=listening)
    env = headless_route.child_env({}, port=listening, user_store=_store(planted))
    routed = env.get(TARGET) == planted
    assert routed


def test_a_mixed_case_target_in_the_base_is_replaced(
    monkeypatch: pytest.MonkeyPatch, listening: int
) -> None:
    """Windows compares names without case, so a variant key must not survive beside ours."""
    monkeypatch.delenv(SOURCE, raising=False)
    planted = _url(listening)
    env = headless_route.child_env(
        {"Anthropic_Base_Url": "planted-stale"}, port=listening, user_store=_store(planted)
    )
    variants = [key for key in env if key.upper() == TARGET]
    only_ours = variants == [TARGET] and env[TARGET] == planted
    assert only_ours


def test_a_refusal_never_carries_the_value(monkeypatch: pytest.MonkeyPatch, dead_port: int) -> None:
    """The reason names the variable and never embeds the value it holds."""
    monkeypatch.delenv(SOURCE, raising=False)
    marker = "plantedmarkerhost"
    planted = f"http://{marker}:{dead_port}"
    with pytest.raises(headless_route.HeadlessRouteRefused) as caught:
        headless_route.child_env({}, port=dead_port, user_store=_store(planted))
    leaked = marker in caught.value.reason or marker in str(caught.value)
    assert not leaked


@pytest.mark.skipif(sys.platform != "win32", reason="the user store is the Windows registry")
def test_the_real_store_reader_answers_none_for_an_absent_name() -> None:
    """An absent name is None (readable, absent), never the unreadable error."""
    got = headless_route.user_store_value("CS_1225_SURELY_UNSET_NAME")
    is_none = got is None
    assert is_none


@pytest.mark.skipif(sys.platform == "win32", reason="off Windows there is no store")
def test_off_windows_the_store_is_unreadable() -> None:
    with pytest.raises(headless_route.UserStoreUnreadableError):
        headless_route.user_store_value(SOURCE)


@pytest.mark.parametrize(
    ("returncode", "output", "expected"),
    [
        (0, '{"type":"result","is_error":false}', "ok"),
        (1, '{"type":"result","is_error":true,"api_error_status":429}', "usage_limit"),
        (1, "Claude AI usage limit reached|1760000000", "failed"),
        (1, "API Error: 429 rate_limit_error", "failed"),
        (1, "result 429 somewhere in prose", "failed"),
        (1, '{"type":"result","is_error":true,"api_error_status":"429"}', "failed"),
        (1, '{"type":"result","is_error":true,"api_error_status":429,"num_turns":7}', "failed"),
        (
            1,
            '{"type":"result","is_error":true,"api_error_status":429,"total_cost_usd":1.5}',
            "failed",
        ),
        (
            1,
            '{"type":"result","is_error":true,"api_error_status":429,"num_turns":1,'
            '"total_cost_usd":0}',
            "usage_limit",
        ),
        (1, "some other crash", "failed"),
        (2, "", "failed"),
        (0, "usage limit reached", "ok"),
        (0, '{"type":"result","is_error":true,"api_error_status":429}', "usage_limit"),
        (0, '{"type":"result","is_error":false,"api_error_status":429}', "ok"),
    ],
)
def test_classify_exit(returncode: int, output: str, expected: str) -> None:
    """A non-zero exit with a usage-limit marker backs off; any other non-zero failed."""
    assert headless_route.classify_exit(returncode, output) == expected


# ---------------------------------------------------------------------------
# The lane launcher's spawn is routed, and refuses without spawning.
# ---------------------------------------------------------------------------


class _PopenSpy:
    """Records every construction and starts nothing."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def __call__(self, argv: list[str], **kwargs: object) -> object:
        del argv
        self.calls.append(dict(kwargs))
        raise OSError(0, "spy refuses to start anything")


def _spawn_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    runner = tmp_path / "run_lane.ps1"
    runner.write_bytes(b"# synthetic\n")
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(b"# synthetic\n")
    return runner, prompt, tmp_path, tmp_path / "lane.log"


def test_the_lane_spawn_refuses_without_spawning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No route: the launcher refuses, names the variable, and Popen is never reached."""
    from ops.loop import lane_launcher  # noqa: PLC0415 - the module under test

    spy = _PopenSpy()
    monkeypatch.setattr(lane_launcher.subprocess, "Popen", spy)
    monkeypatch.setattr(lane_launcher, "resolve_tool", lambda _name: "synthetic-shell")
    monkeypatch.setattr(lane_launcher.headless_route, "user_store_value", lambda _name: None)
    monkeypatch.delenv(SOURCE, raising=False)
    with pytest.raises(lane_launcher.LaneLaunchError) as caught:
        lane_launcher._spawn(*_spawn_inputs(tmp_path))  # noqa: SLF001 - the seam under test
    reason = caught.value.reason
    names_var = SOURCE in str(caught.value)
    spawned = len(spy.calls)
    assert (reason, names_var, spawned) == (lane_launcher.REASON_SPAWN_FAILED, True, 0)


def test_the_lane_spawn_hands_the_child_the_routed_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With a route, the env Popen receives is exactly what child_env built."""
    from ops.loop import lane_launcher  # noqa: PLC0415 - the module under test

    spy = _PopenSpy()
    routed = {"PLANTED_ROUTE_MARKER": "1"}
    handed: list[object] = []

    def fake_child_env(base: object, **_kw: object) -> dict[str, str]:
        handed.append(base)
        return dict(routed)

    monkeypatch.setattr(lane_launcher.subprocess, "Popen", spy)
    monkeypatch.setattr(lane_launcher, "resolve_tool", lambda _name: "synthetic-shell")
    monkeypatch.setattr(lane_launcher.headless_route, "child_env", fake_child_env)
    with pytest.raises(lane_launcher.LaneLaunchError):
        lane_launcher._spawn(*_spawn_inputs(tmp_path))  # noqa: SLF001 - the seam under test
    got_env = [call.get("env") for call in spy.calls]
    was_routed = got_env == [routed]
    from_environ = len(handed) == 1 and handed[0] is os.environ
    assert (was_routed, from_environ) == (True, True)


# ---------------------------------------------------------------------------
# The PowerShell runner refuses an unrouted start without running the CLI.
# ---------------------------------------------------------------------------

RUNNER: Final = ROOT / "ops" / "loop" / "run_lane.ps1"
_CHILD_TIMEOUT_S: Final = 120
_REFUSED_EXIT: Final = 3
#: A SYNTHETIC value in the allowlisted shape. The shim CLI never connects to it.
_RUNNER_GOOD: Final = "http://localhost:3456/synthetic/route"


#: The default shim: it leaves one marker file behind and exits 0.
_SHIM_RAN: Final = b'@echo ran> "%~dp0ran.txt"\r\n@exit /b 0\r\n'


def _run_runner(
    tmp_path: Path,
    *,
    value: str | None,
    shim: bytes = _SHIM_RAN,
    extra_env: dict[str, str] | None = None,
) -> tuple[int, bool, list[str]]:
    """Run the real runner over a shim; return exit code, whether the shim ran, log lines.

    CS-1231 slice C: the runner's direct child is the fleet kit's interpreter,
    which starts the CLI, so the shim stands where that interpreter stands.
    """
    shell = shutil.which("powershell")
    if shell is None:
        pytest.skip("Windows PowerShell is not on PATH")
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir()
    marker = shim_dir / "ran.txt"
    (shim_dir / "python.cmd").write_bytes(shim)
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(b"# synthetic\n")
    tree = tmp_path / "tree"
    tree.mkdir()
    log = tmp_path / "lane.log"
    system = Path(os.environ.get("SYSTEMROOT") or r"C:\Windows") / "System32"
    env = {key: val for key, val in os.environ.items() if key.upper() != TARGET}
    env = {key: val for key, val in env.items() if key.upper() != "PATH"}
    env["PATH"] = f"{shim_dir}{os.pathsep}{system}"
    if value is not None:
        env[TARGET] = value
    env.update(extra_env or {})
    argv = [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(RUNNER)]
    argv += ["-PromptFile", str(prompt), "-Cwd", str(tree), "-Log", str(log)]
    done = subprocess.run(
        argv,
        capture_output=True,
        check=False,
        timeout=_CHILD_TIMEOUT_S,
        env=env,
    )
    text = log.read_bytes().decode("utf-8-sig", errors="replace") if log.is_file() else ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return done.returncode, marker.is_file(), lines


@pytest.mark.skipif(sys.platform != "win32", reason="the runner is Windows PowerShell")
def test_the_runner_refuses_an_unrouted_start_without_running_the_cli(tmp_path: Path) -> None:
    """Empty ANTHROPIC_BASE_URL: exit non-zero, the shim never ran, both lines written."""
    code, ran, lines = _run_runner(tmp_path, value=None)
    refused = any(line.startswith("lane refused") and TARGET in line for line in lines)
    exit_line = bool(lines) and lines[-1].startswith("lane exit") and lines[-1].endswith("code=3")
    assert (code, ran, refused, exit_line) == (_REFUSED_EXIT, False, True, True)


@pytest.mark.skipif(sys.platform != "win32", reason="the runner is Windows PowerShell")
def test_control_a_routed_start_reaches_the_kit(tmp_path: Path) -> None:
    """THE CONTROL: the same harness with the variable set does run the shim."""
    code, ran, lines = _run_runner(tmp_path, value=_RUNNER_GOOD)
    refused = any(line.startswith("lane refused") for line in lines)
    assert (code, ran, refused) == (0, True, False)


@pytest.mark.skipif(sys.platform != "win32", reason="the runner is Windows PowerShell")
@pytest.mark.parametrize(
    "planted",
    [
        "http://evil.example" + _BACKSLASH + "@127.0.0.1:3456",
        "http://user:pw@localhost:3456",
        "http://localhost:3456/a?x=1",
        "http://localhost:3457",
        "http://evil.example:3456",
    ],
    ids=["backslash-at", "userinfo", "query", "other-port", "remote-host"],
)
def test_the_runner_refuses_a_value_outside_the_allowlist(tmp_path: Path, planted: str) -> None:
    """The fallback check is the same whole-string shape, not merely non-empty."""
    code, ran, lines = _run_runner(tmp_path, value=planted)
    refused = any(line.startswith("lane refused") and TARGET in line for line in lines)
    leaked = any("evil" in line or "pw" in line for line in lines)
    assert (code, ran, refused, leaked) == (_REFUSED_EXIT, False, True, False)


# ---------------------------------------------------------------------------
# CS-1282 - the lane worker runs with the kit's SUBAGENT-FIRST hook OFF.
# ---------------------------------------------------------------------------
# The fleet kit's PreToolUse hook (v10, carried at v11) denies every guarded
# tool in a thread with no agent id, and DEFAULTS TO DENY when its mode file is absent. That file is
# gitignored, so a lane worktree never has one. A headless lane worker has no
# operator and no main pane, so the grant (docs/LEDGER.md, "2026-10-08 -
# CS-1282") conditions the hook's wiring on the runner setting it off. Since
# CS-1231 slice C the runner starts the kit's spawn command line, whose child
# env turns the hook off for the CLI too; the runner's own assignment stays as
# defence in depth, and both halves are graded here.

#: The one accepted spelling: a literal, double-quoted assignment at script scope.
_SUBAGENT_FIRST_OFF: Final = f'$env:{subagent_first.ENV_MODE} = "off"'
#: The runner's single start, the call operator on the resolved interpreter that
#: runs the kit's spawn command line.
_INVOCATION: Final = re.compile(r"&\s*\$python\b", re.IGNORECASE)
#: A shim that records the mode it was handed. "echo mode=" and never a bare
#: echo, because a batch "echo off" toggles echoing instead of printing.
_SHIM_MODE: Final = b'@echo mode=%FLEET_SUBAGENT_FIRST%> "%~dp0ran.txt"\r\n@exit /b 0\r\n'


def test_the_lane_runner_turns_the_subagent_first_hook_off_before_the_cli() -> None:
    """STATIC, so it runs everywhere: one assignment, the kit's own off, before the invocation."""
    lines = RUNNER.read_bytes().decode("ascii").split("\n")
    mentions = [i for i, line in enumerate(lines) if subagent_first.ENV_MODE in line]
    assigned = [i for i in mentions if lines[i] == _SUBAGENT_FIRST_OFF]
    invoked = [i for i, line in enumerate(lines) if _INVOCATION.search(line)]
    before = len(assigned) == 1 and len(invoked) == 1 and assigned[0] < invoked[0]
    off_is_a_kit_mode = "off" in subagent_first.MODES
    kit_spawn_agrees = kit.child_env(_url(1), parent={}).get(subagent_first.ENV_MODE) == "off"
    assert (len(assigned), mentions == assigned, before, off_is_a_kit_mode, kit_spawn_agrees) == (
        1,
        True,
        True,
        True,
        True,
    )


@pytest.mark.skipif(sys.platform != "win32", reason="the runner is Windows PowerShell")
def test_the_lane_worker_receives_the_subagent_first_hook_off(tmp_path: Path) -> None:
    """RUNTIME: the runner's own env is POISONED with deny; the child must see off."""
    code, ran, _ = _run_runner(
        tmp_path,
        value=_RUNNER_GOOD,
        shim=_SHIM_MODE,
        extra_env={subagent_first.ENV_MODE: "deny"},
    )
    said = (tmp_path / "shim" / "ran.txt").read_bytes().decode("ascii", "replace").strip()
    assert (code, ran, said) == (0, True, "mode=off")


@pytest.mark.parametrize(
    "name",
    ["CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY"],
)
def test_a_provider_switch_is_dropped_from_the_child(
    monkeypatch: pytest.MonkeyPatch, listening: int, name: str
) -> None:
    """A provider switch would send the child past the proxy; it never reaches it."""
    monkeypatch.delenv(SOURCE, raising=False)
    base = {name: "1", name.lower(): "1", "KEEP_ME": "1"}
    env = headless_route.child_env(base, port=listening, user_store=_store(_url(listening)))
    survivors = sorted(key for key in env if key.upper() == name)
    kept = env.get("KEEP_ME") == "1"
    assert (survivors, kept) == ([], True)


@pytest.mark.parametrize(
    ("shape", "probed"),
    [
        ("http://127.0.0.1:{port}", "127.0.0.1"),
        ("http://localhost:{port}/a/b", "localhost"),
        ("http://[::1]:{port}/x", "::1"),
    ],
)
def test_the_probe_targets_the_host_the_value_names(
    monkeypatch: pytest.MonkeyPatch, listening: int, shape: str, probed: str
) -> None:
    """The liveness connect goes where the child will go, not to a fixed host."""
    monkeypatch.delenv(SOURCE, raising=False)
    seen: list[tuple[str, int]] = []

    def recording(address: tuple[str, int], timeout: float) -> socket.socket:
        seen.append((address[0], address[1] + int(timeout * 0)))
        return socket.create_connection(("127.0.0.1", listening), timeout=timeout)

    headless_route.child_env(
        {}, port=listening, user_store=_store(shape.format(port=listening)), connect=recording
    )
    assert seen == [(probed, listening)]
