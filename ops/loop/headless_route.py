r"""CS-1225 - route every headless `claude` spawn through the local proxy, or refuse.

OPERATOR RULING, 2026-10-02 (recorded in docs/LEDGER.md): every headless CLI
process this tree starts runs against a SECOND subscription, reached through a
proxy listening on loopback. This module is the one place that decision is
applied, so a spawn site never spells the route itself.

`child_env(base_env)` returns a COPY of `base_env` with `ANTHROPIC_BASE_URL` set
to the value of `CLAUDE_HEADLESS_BASE_URL`. The value is read AT CALL TIME from
the user environment store first (`HKEY_CURRENT_USER\Environment`) and from the
process environment only when the store holds nothing, because a long-lived
parent - a scheduled task, the queue driver - carries the copy it inherited at
its own start, and a value the operator set since would otherwise never reach a
child. Nothing here mutates `os.environ` or writes any variable at any scope.

FAIL CLOSED, NO FALLBACK. An unset or blank variable, a value that does not
name the loopback proxy, or a proxy that refuses or times out a TCP connect
raises `HeadlessRouteRefused`. There is no retry another way and no spawn on
the account the parent happens to be logged into: a child that silently ran on
the primary subscription is exactly the outcome the ruling exists to prevent.
The proxy's own auto-fallback mode is never invoked from this tree.

AN INHERITED API KEY IS DROPPED from the copy. The CLI prefers a key over any
login, and a key at machine scope is inherited by every child - measured once
already in `ops/loop/run_lane.ps1`, where a lane died on "credit balance too
low". A routed child must ride the proxy, not whatever key is lying around.

NO VALUE IN ANY REASON (CLAUDE.md rules 12 and 13). A refusal's `reason` is an
authored phrase that NAMES the variable and never embeds what it holds; callers
print `.reason`, never the exception object.

`classify_exit(returncode, output)` maps a finished child to `ok`,
`usage_limit` or `failed`. A usage-limit refusal is the account saying no, and
a caller that respawned on it would hammer the same refusal - so it is its own
outcome, which every caller honours with a back-off rather than a retry.
"""

from __future__ import annotations

import json
import os
import re
import socket
import sys
from collections.abc import Callable, Mapping
from typing import Final
from urllib.parse import urlsplit

#: The variable the operator sets, naming the proxy.
SOURCE_VAR: Final = "CLAUDE_HEADLESS_BASE_URL"

#: The variable the child CLI reads its API base from.
TARGET_VAR: Final = "ANTHROPIC_BASE_URL"

#: Dropped from every routed child - see the module docstring.
DROPPED_VARS: Final = ("ANTHROPIC_API_KEY",)

#: The ruled proxy endpoint. Tests inject a port; production never does.
PROXY_HOST: Final = "127.0.0.1"
PROXY_PORT: Final = 3456

#: How long the liveness connect may take before the proxy counts as down.
CONNECT_TIMEOUT_S: Final = 2.0

#: Host spellings that name the loopback proxy.
LOOPBACK_HOSTS: Final = frozenset({"127.0.0.1", "localhost", "::1"})

REASON_UNSET: Final = f"{SOURCE_VAR} is unset or empty in the user store and the process"
REASON_NOT_LOCAL: Final = f"{SOURCE_VAR} does not name the loopback proxy endpoint"
REASON_PROXY_DOWN: Final = (
    f"the proxy {SOURCE_VAR} names is not accepting connections on its loopback port"
)

OUTCOME_OK: Final = "ok"
OUTCOME_USAGE_LIMIT: Final = "usage_limit"
OUTCOME_FAILED: Final = "failed"

#: The HTTP status of a usage-limit refusal, as a run's result reports it.
_USAGE_LIMIT_STATUS: Final = 429

#: Text markers of a usage or rate limit, for output that is not a result object.
_LIMIT_MARKERS: Final = re.compile(
    r"usage limit|rate limit|rate_limit|limit reached|limit will reset|\b429\b",
    re.IGNORECASE,
)

_REG_EXPAND_SZ: Final = 2


class HeadlessRouteRefused(RuntimeError):  # noqa: N818 - the ruled name
    """The route could not be established; the spawn must not happen.

    ``reason`` is an authored, value-free phrase. Print it, never the object.
    """

    def __init__(self, reason: str) -> None:
        """Record the authored reason."""
        super().__init__(reason)
        self.reason = reason


def user_store_value(name: str) -> str | None:
    """The named variable from the USER environment store, or None. Never raises.

    Args:
        name: The variable name.

    Returns:
        The stored string, expanded when stored as an expandable string, or
        None off Windows, when absent, or on any read fault.
    """
    if sys.platform != "win32":
        return None
    try:
        import winreg  # noqa: PLC0415 - Windows-only, deferred so import stays portable

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, kind = winreg.QueryValueEx(key, name)
    except OSError:
        return None
    if not isinstance(value, str):
        return None
    if kind == _REG_EXPAND_SZ:
        return os.path.expandvars(value)
    return value


def _read_source(user_store: Callable[[str], str | None]) -> str:
    """The route value, user store first. Raises when neither store holds one."""
    stored = user_store(SOURCE_VAR)
    if stored is not None and stored.strip():
        return stored.strip()
    process = os.environ.get(SOURCE_VAR, "")
    if process.strip():
        return process.strip()
    raise HeadlessRouteRefused(REASON_UNSET)


def _names_proxy(value: str, port: int) -> bool:
    """Whether ``value`` is an http(s) URL naming the loopback proxy on ``port``."""
    try:
        parts = urlsplit(value)
        named_port = parts.port
    except ValueError:
        return False
    host = (parts.hostname or "").lower()
    return parts.scheme in ("http", "https") and host in LOOPBACK_HOSTS and named_port == port


def child_env(
    base_env: Mapping[str, str],
    *,
    host: str = PROXY_HOST,
    port: int = PROXY_PORT,
    user_store: Callable[[str], str | None] | None = None,
    connect: Callable[..., socket.socket] | None = None,
) -> dict[str, str]:
    """A COPY of ``base_env`` routed through the proxy. Refuses rather than fall back.

    Args:
        base_env: The environment to copy. Never mutated.
        host: The proxy host to probe. Tests only.
        port: The proxy port to probe and to require in the value. Tests only.
        user_store: Reads one variable from the user store, or None for
            :func:`user_store_value` looked up AT CALL TIME. Tests only.
        connect: Opens the liveness connection, or None for
            ``socket.create_connection`` looked up at call time. Tests only.

    Returns:
        The routed environment.

    Raises:
        HeadlessRouteRefused: The variable is unset, does not name the proxy,
            or the proxy is not accepting connections.
    """
    reader = user_store_value if user_store is None else user_store
    opener = socket.create_connection if connect is None else connect
    value = _read_source(reader)
    if not _names_proxy(value, port):
        raise HeadlessRouteRefused(REASON_NOT_LOCAL)
    try:
        connection = opener((host, port), timeout=CONNECT_TIMEOUT_S)
    except OSError:
        # The cause is dropped on purpose: a socket error can render the address
        # it failed on, and the reason above already says everything safe.
        raise HeadlessRouteRefused(REASON_PROXY_DOWN) from None
    connection.close()
    dropped = {TARGET_VAR, *DROPPED_VARS}
    env = {key: val for key, val in base_env.items() if key.upper() not in dropped}
    env[TARGET_VAR] = value
    return env


def _result_says_limit(output: str) -> bool:
    """Whether any JSON line of ``output`` is a result object carrying a 429."""
    for line in output.splitlines():
        candidate = line.strip().lstrip("\ufeff")
        if not candidate.startswith("{"):
            continue
        try:
            parsed = json.loads(candidate)
        except (ValueError, RecursionError):
            continue
        if type(parsed) is dict and parsed.get("api_error_status") == _USAGE_LIMIT_STATUS:
            return True
    return False


def classify_exit(returncode: int | None, output: str) -> str:
    """Map a finished child to ``ok``, ``usage_limit`` or ``failed``.

    Args:
        returncode: The child's exit code; None counts as a failure.
        output: Everything the child printed. Read to classify, never rendered.

    Returns:
        One of the three OUTCOME_ constants.
    """
    if returncode == 0:
        return OUTCOME_OK
    text = output if isinstance(output, str) else ""
    if _result_says_limit(text) or _LIMIT_MARKERS.search(text):
        return OUTCOME_USAGE_LIMIT
    return OUTCOME_FAILED
