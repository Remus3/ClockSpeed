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
import socket
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
    assert headless_route.PROXY_HOST == "127.0.0.1"
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


def test_the_process_env_is_the_fallback(monkeypatch: pytest.MonkeyPatch, listening: int) -> None:
    """With nothing in the user store, the process copy is read."""
    planted = _url(listening)
    monkeypatch.setenv(SOURCE, planted)
    env = headless_route.child_env({}, port=listening, user_store=_store(None))
    fell_back = env.get(TARGET) == planted
    assert fell_back


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


def test_the_real_store_reader_answers_none_or_a_string() -> None:
    """The default reader never raises, whatever this box holds. Its value is never shown."""
    got = headless_route.user_store_value("CS_1225_SURELY_UNSET_NAME")
    is_none = got is None
    assert is_none


@pytest.mark.parametrize(
    ("returncode", "output", "expected"),
    [
        (0, '{"type":"result","is_error":false}', "ok"),
        (1, '{"type":"result","is_error":true,"api_error_status":429}', "usage_limit"),
        (1, "Claude AI usage limit reached|1760000000", "usage_limit"),
        (1, "API Error: 429 rate_limit_error", "usage_limit"),
        (1, "some other crash", "failed"),
        (2, "", "failed"),
        (0, "usage limit reached", "ok"),
    ],
)
def test_classify_exit(returncode: int, output: str, expected: str) -> None:
    """A non-zero exit with a usage-limit marker backs off; any other non-zero failed."""
    assert headless_route.classify_exit(returncode, output) == expected
