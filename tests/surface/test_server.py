"""CS-601 slice S2 - the loopback TLS listener, its providers, and its log channel.

What is covered, and the authority for each arm:

a. THE LISTENER IS RELEASED ON EVERY EXIT PATH, INCLUDING AN EXCEPTION RAISED
   INSIDE THE BLOCK. Proved by connecting a second time and asserting the
   connection is REFUSED, rather than by asserting a flag the code sets about
   itself. A port still held by a process that stopped answering on it is the
   failure that makes the next start impossible.
b. A BIND FAILURE NEVER FALLS BACK. The refusal names the port it wanted, points
   at the allocation record and the environment check, and returns a non-zero
   exit code. One arm asserts no OTHER port was bound, because "started
   somewhere" is the process-level shape of the plausible-rather-than-honest
   answer this project refuses everywhere else.
c. TRAVERSAL CANNOT RESOLVE BECAUSE THERE IS NO RESOLUTION STEP. The static
   surface is a frozen three-name table and the API surface is exact matching
   against authored templates, so ``/../../work/x.sav`` is not normalised away -
   it is simply not equal to any of them. The arms assert 404 AND assert the
   answer names ``ENDPOINT_UNROUTED`` rather than the path that was asked for.
d. REQUEST CONTENT ESCAPES ON TWO CHANNELS, AND BOTH ARE SWEPT. A canary is
   planted in a query string, in a header and in four malformed request lines;
   stderr is asserted to carry it zero times, AND SO IS EVERY RESPONSE BYTE. The
   second sweep exists because the first one alone was not enough: replacing
   ``send_error`` with the stdlib's - which interpolates the request line into
   the reason phrase - passed all 85 arms, because that leak goes to the response
   BODY and every arm was reading stderr. MEASURED by mutation, not reasoned.
   Each sweep has its own NEGATIVE CONTROL, a handler with the stdlib method
   restored, asserted to FIND the canary - without them, a broken sweep and a
   clean server produce the same green.
   ``log_error`` is graded STRUCTURALLY and the arm says so: nothing calls it
   while ``send_error`` is overridden, so no runtime arm can reach it.
e. THE LAYER WRITES NOTHING AND COMPUTES NOTHING. Two static sweeps over
   ``clockspeed/surface/**.py``, each run against a planted positive so a sweep
   that looks for nothing is distinguishable from a layer that does nothing.
f. A PROVIDER ANSWERS ``None`` RATHER THAN RAISING. "No game installed" and "no
   save yet" are true answers about a working system, and every arm below runs
   with NO GAME INSTALLED - BOOTSTRAP.md section 8.1 requires that of the whole
   rule suite, which is why the providers take injectable seams.

Test-quality discipline (CONVENTIONS.md section 7.2). Every sweep binds its
population size to a scalar and asserts the expected count BEFORE it iterates.
Every absence is asserted on a scalar, never on the collection: pytest renders
the asserted EXPRESSION independently of the message, so asserting on a list of
offending paths PRINTS those paths - which is how this repository once shipped a
path leak inside its own PII guard. Every port below is bound as
``("127.0.0.1", 0)`` and read back from ``server_address``; the allocated number
appears in no test in this package, and ``test_config.py`` sweeps for it.
"""

from __future__ import annotations

import ast
import http.client
import socket
import ssl
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.surface import config, providers, server
from clockspeed.surface.api import contract

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Every listener in this module asks the kernel for a port. The allocated one
#: is never bound by a test - it may be in use by the operator's own dashboard,
#: and a test that fights it is a test that fails for an unrelated reason.
EPHEMERAL: Final = 0

#: A string that appears in no path, no header and no route in this repository.
CANARY: Final = "zqxjcanary601s2"

#: Bounds on anything that talks to a socket, so a hang is a failure rather than
#: a hung suite.
CLIENT_TIMEOUT: Final = 10.0
CONNECT_TIMEOUT: Final = 2.0
SETTLE_TIMEOUT: Final = 5.0

#: The route every arm that needs a live endpoint registers.
PROBE_TEMPLATE: Final = "/api/probe"

#: The shipped layer both static sweeps walk.
SURFACE_ROOT: Final = Path(__file__).resolve().parents[2] / "clockspeed" / "surface"

#: Modules outside ``api/`` allowed to name a filesystem read. Asserted as an
#: EQUALITY, not a subset: a module dropping off the list is as much a finding as
#: one joining it, because it means the read moved somewhere unmeasured.
READERS_ALLOWED: Final = frozenset({"config.py", "providers.py"})

#: How few modules make the sweeps meaningless. A sweep over an empty population
#: passes vacuously, so each asserts this floor before it iterates.
MIN_SURFACE_MODULES: Final = 5
MIN_ENDPOINT_MODULES: Final = 2

#: The whole static surface, as a count an arm asserts rather than a literal
#: buried inside one.
STATIC_SURFACE_SIZE: Final = 3

#: Header names every answer carries, whatever its status.
FIXED_HEADER_NAMES: Final = ("cache-control", "x-content-type-options", "referrer-policy")

#: Names carrying a separator, each of which REALLY ESCAPES a directory on this
#: filesystem. Handed to the asset reader's closed set ON PURPOSE, so the arm
#: grades the SECOND gate rather than the allow-list. They must resolve to a
#: file that exists - see the arm for what went wrong when they did not.
SEPARATOR_NAMES: Final = ("../secret.json", "..\\secret.json", "a/../../secret.json")

#: What the escape targets contain, so reaching one is distinguishable from
#: reading anything else.
OUTSIDE_BYTES: Final = b"OUTSIDE-THE-WEB-DIRECTORY"


# ---------------------------------------------------------------------------
# Detectors. Each proves an absence, so each is run against a planted positive.
# ---------------------------------------------------------------------------

#: Method names whose only meaning is a filesystem mutation. ``write`` and
#: ``replace`` are DELIBERATELY ABSENT: ``wfile.write`` is a socket and
#: ``str.replace`` is a string, and a detector with false positives gets
#: weakened by whoever hits one first.
WRITE_METHODS: Final = frozenset(
    {
        "copy2",
        "copyfile",
        "copyfileobj",
        "copytree",
        "hardlink_to",
        "makedirs",
        "mkdir",
        "removedirs",
        "rmdir",
        "rmtree",
        "symlink_to",
        "touch",
        "unlink",
        "write_bytes",
        "write_text",
    }
)

#: Names that mutate only when reached through ``os`` or ``shutil``, where the
#: receiver disambiguates them.
QUALIFIED_WRITE_NAMES: Final = frozenset(
    {"chmod", "move", "remove", "rename", "replace", "rmdir", "truncate", "unlink"}
)
WRITE_RECEIVERS: Final = frozenset({"os", "shutil"})

#: Names that read the filesystem. The allow-list arm counts modules carrying one.
READ_NAMES: Final = frozenset(
    {"glob", "iterdir", "listdir", "open", "read_bytes", "read_text", "rglob", "scandir"}
)

#: Arithmetic that derives a quantity. ``surface/ never computes``
#: (``clockspeed/surface/__init__.py``).
ARITHMETIC_OPS: Final = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)


def _callee(node: ast.Call) -> tuple[str | None, str | None]:
    """The (receiver, name) of a call, as far as a name can be recovered.

    Args:
        node: The call.

    Returns:
        (receiver name or None, callee name or None).
    """
    func = node.func
    if isinstance(func, ast.Attribute):
        receiver = func.value.id if isinstance(func.value, ast.Name) else None
        return receiver, func.attr
    if isinstance(func, ast.Name):
        return None, func.id
    return None, None


def _write_mode(node: ast.Call) -> bool:
    """Whether an ``open`` call names a mode that can modify a file.

    Args:
        node: A call already known to be named ``open``.

    Returns:
        True when a mode argument carries w, a, x or +.
    """
    candidates = list(node.args[1:]) + [kw.value for kw in node.keywords]
    return any(
        isinstance(candidate, ast.Constant)
        and isinstance(candidate.value, str)
        and any(flag in candidate.value for flag in ("w", "a", "x", "+"))
        for candidate in candidates
    )


def writes_in(source: str) -> list[int]:
    """Every line in ``source`` that mutates the filesystem.

    Args:
        source: Python source text.

    Returns:
        The offending line numbers.
    """
    found: list[int] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        receiver, name = _callee(node)
        mutates = (
            name in WRITE_METHODS
            or (receiver in WRITE_RECEIVERS and name in QUALIFIED_WRITE_NAMES)
            or (name == "open" and _write_mode(node))
        )
        if mutates:
            found.append(node.lineno)
    return found


def reads_in(source: str) -> list[int]:
    """Every line in ``source`` that reads the filesystem.

    Args:
        source: Python source text.

    Returns:
        The line numbers, whether or not the module is allowed them.
    """
    return [
        node.lineno
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and _callee(node)[1] in READ_NAMES
    ]


def arithmetic_in(source: str) -> list[int]:
    """Every line in ``source`` deriving a quantity from a number.

    STATED LIMIT, and it is why the numeric-literal condition is there: an
    operator between two NAMES is not graded, because ``required - offered`` is a
    frozenset difference and ``directory / name`` is a path join, and nothing
    static tells either apart from arithmetic. Both shapes are live in this layer
    right now - an endpoint validates parameter names by set difference and this
    layer joins paths - so a rule without the condition would fail correct code
    and get switched off. What IS graded is the shape a derived quantity actually
    takes: an operator with a number written next to it.

    Args:
        source: Python source text.

    Returns:
        The offending line numbers.
    """

    def numeric(node: ast.expr) -> bool:
        return (
            isinstance(node, ast.Constant)
            and isinstance(node.value, int | float)
            and not isinstance(node.value, bool)
        )

    return [
        node.lineno
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.BinOp)
        and isinstance(node.op, ARITHMETIC_OPS)
        and (numeric(node.left) or numeric(node.right))
    ]


def surface_modules() -> list[Path]:
    """Every shipped module in the surface layer.

    Returns:
        The paths, sorted.
    """
    return sorted(SURFACE_ROOT.rglob("*.py"))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def cert_pair(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    """A throwaway certificate and key, minted into a temporary directory.

    Never a tracked file: ``.gitignore`` carries ``*.pem``, and a committed
    private key is the one mistake that cannot be undone by a later commit.
    Minted rather than shipped for the same reason.

    Returns:
        (certificate, key).
    """
    directory = tmp_path_factory.mktemp("s2certs")
    cert = directory / "s2.cert.pem"
    key = directory / "s2.key.pem"
    try:
        finished = subprocess.run(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-keyout",
                str(key),
                "-out",
                str(cert),
                "-days",
                "1",
                "-nodes",
                "-subj",
                "/CN=clockspeed-test",
                "-addext",
                "subjectAltName=IP:127.0.0.1,DNS:localhost",
            ],
            capture_output=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        pytest.skip("openssl could not be run; the TLS arms need a certificate to listen with")
    if finished.returncode != 0 or not cert.is_file() or not key.is_file():
        pytest.skip("openssl did not mint a test certificate")
    return cert, key


@pytest.fixture
def cfg(cert_pair: tuple[Path, Path], tmp_path: Path) -> config.ServerConfig:
    """A configuration bound to an ephemeral port and a temporary asset directory.

    Returns:
        The configuration.
    """
    cert, key = cert_pair
    return config.ServerConfig(
        host=config.LOOPBACK,
        port=EPHEMERAL,
        cert_path=cert,
        key_path=key,
        web_dir=tmp_path / "web",
    )


def probe_route(seen: list[Mapping[str, str]] | None = None) -> contract.Route:
    """A route that answers 200 and records what parameters reached it.

    Args:
        seen: A list to append each call's parameters to, or None.

    Returns:
        The route.
    """

    def handler(parameters: Mapping[str, str]) -> contract.Response:
        if seen is not None:
            seen.append(dict(parameters))
        return contract.ok(PROBE_TEMPLATE, {"probe": True})

    return contract.Route(method="GET", template=PROBE_TEMPLATE, handler=handler)


# ---------------------------------------------------------------------------
# Client helpers. Every one verifies the certificate rather than disabling the
# check - a test that turns verification off cannot tell TLS from plaintext.
# ---------------------------------------------------------------------------


def client_context(cert: Path) -> ssl.SSLContext:
    """A verifying client context trusting exactly the test certificate.

    Args:
        cert: The certificate to trust.

    Returns:
        The context.
    """
    return ssl.create_default_context(cafile=str(cert))


def request(
    port: int,
    path: str,
    cert: Path,
    *,
    method: str = "GET",
    headers: Mapping[str, str] | None = None,
) -> tuple[int, dict[str, str], bytes]:
    """Make one request and read the whole answer.

    Args:
        port: The listening port.
        path: The request path, verbatim and unnormalised.
        cert: The certificate to trust.
        method: The HTTP method.
        headers: Extra request headers.

    Returns:
        (status, headers, body).
    """
    conn = http.client.HTTPSConnection(
        config.LOOPBACK, port, context=client_context(cert), timeout=CLIENT_TIMEOUT
    )
    try:
        conn.request(method, path, headers=dict(headers or {}))
        answer = conn.getresponse()
        return answer.status, {k.lower(): v for k, v in answer.getheaders()}, answer.read()
    finally:
        conn.close()


def raw_over_tls(port: int, cert: Path, payload: bytes) -> bytes:
    """Push raw bytes through the handshake, bypassing every client-side check.

    This is how a malformed request LINE is delivered - ``http.client`` will not
    build one, and the malformed line is exactly the input that drives the
    stdlib's echoing error paths.

    Args:
        port: The listening port.
        cert: The certificate to trust.
        payload: The bytes to send.

    READ TO END OF STREAM, NOT ONE ``recv``. A single read returned the header
    block alone and left a 146-byte body on the socket, which made twelve arms
    fail while the server was answering correctly - the assertion was about the
    size of one TCP segment. Every request here sends ``Connection: close``, so
    the server closes and the loop terminates.

    Returns:
        Whatever came back, possibly empty.
    """
    context = client_context(cert)
    chunks: list[bytes] = []
    deadline = time.monotonic() + CLIENT_TIMEOUT
    try:
        with (
            socket.create_connection((config.LOOPBACK, port), timeout=CLIENT_TIMEOUT) as raw,
            context.wrap_socket(raw, server_hostname=config.LOOPBACK) as tls,
        ):
            tls.sendall(payload)
            while time.monotonic() < deadline:
                piece = tls.recv(65536)
                if not piece:
                    break
                chunks.append(piece)
    except OSError:
        pass
    return b"".join(chunks)


def raw_get(port: int, cert: Path, path: str) -> tuple[int, bytes]:
    """Send a GET whose path reaches the server BYTE FOR BYTE.

    ``http.client`` normalises what it is given - MEASURED here, where it
    collapsed ``//app.js`` to ``/app.js`` and turned an arm that meant to prove
    the server refuses a path into one that proved the client rewrote it. Every
    traversal arm goes through this instead, so what is graded is this server's
    matching and not the client library's tidying.

    Args:
        port: The listening port.
        cert: The certificate to trust.
        path: The request path, delivered verbatim.

    Returns:
        (status code, the whole raw answer). The status is zero when nothing
        resembling an HTTP answer came back.
    """
    payload = f"GET {path} HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
    answer = raw_over_tls(port, cert, payload.encode("ascii"))
    if not answer.startswith(b"HTTP/"):
        return 0, answer
    try:
        return int(answer.split(b" ", 2)[1]), answer
    except (IndexError, ValueError):
        return 0, answer


@contextmanager
def serving_handler(
    cfg: config.ServerConfig, handler_class: type[BaseHTTPRequestHandler]
) -> Iterator[int]:
    """Serve with a DELIBERATELY LEAKY handler, for the negative controls.

    ``serve`` hardwires the real handler - correctly, since the handler is not a
    caller's choice in production. A planted leak therefore has to stand the
    listener up by hand. The lifetime discipline mirrors ``serve`` exactly, so a
    control that fails does not also leak a port into the rest of the suite.

    Args:
        cfg: Supplies the certificate pair.
        handler_class: The handler to serve with.

    Yields:
        The bound port.
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cfg.cert_path, cfg.key_path)
    listener = server.DashboardServer(
        (config.LOOPBACK, EPHEMERAL), handler_class, server.routing([probe_route()]), None
    )
    listener.socket = context.wrap_socket(listener.socket, server_side=True)
    thread = threading.Thread(
        target=listener.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True
    )
    thread.start()
    try:
        yield listener.server_address[1]
    finally:
        stopper = threading.Thread(target=listener.shutdown, daemon=True)
        stopper.start()
        stopper.join(SETTLE_TIMEOUT)
        listener.server_close()
        thread.join(SETTLE_TIMEOUT)


def raw_head(port: int, cert: Path, path: str) -> bytes:
    """Send a HEAD and return every byte the server actually wrote.

    ``http.client`` sets a HEAD response's length to zero and never reads the
    socket, so ``response.read()`` returns empty WHATEVER the server sent -
    MEASURED, by a mutation that wrote the body on a HEAD and passed all 87
    arms. Reading the socket directly is the only way to grade what was written.

    Args:
        port: The listening port.
        cert: The certificate to trust.
        path: The request path.

    Returns:
        The whole raw answer.
    """
    payload = f"HEAD {path} HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
    return raw_over_tls(port, cert, payload.encode("ascii"))


def connect_refused(port: int) -> bool:
    """Whether nothing is listening on a port.

    Args:
        port: The port to probe.

    Returns:
        True when the connection was refused.
    """
    try:
        with socket.create_connection((config.LOOPBACK, port), timeout=CONNECT_TIMEOUT):
            return False
    except OSError:
        return True


def held_port() -> Iterator[int]:
    """Hold a listening socket and yield its port.

    Returns:
        An iterator yielding the held port.
    """
    holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    holder.bind((config.LOOPBACK, EPHEMERAL))
    holder.listen(1)
    try:
        yield holder.getsockname()[1]
    finally:
        holder.close()


@pytest.fixture
def occupied() -> Iterator[int]:
    """A port another socket in this process is actively listening on.

    Returns:
        An iterator yielding the occupied port.
    """
    yield from held_port()


# ---------------------------------------------------------------------------
# (a) TLS, and the listener is released on every exit path
# ---------------------------------------------------------------------------


def test_the_listener_binds_an_ephemeral_port_and_answers_over_verified_tls(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    with server.serve(cfg, [probe_route()]) as running:
        port = running.server_address[1]
        assert port != EPHEMERAL, "the kernel did not hand back a real port"
        status, _headers, body = request(port, PROBE_TEMPLATE, cert)
    assert status == contract.HTTP_OK
    assert b'"status":"ok"' in body


def test_plaintext_is_not_answered_on_the_tls_listener(cfg: config.ServerConfig) -> None:
    with server.serve(cfg, [probe_route()]) as running:
        port = running.server_address[1]
        try:
            with socket.create_connection((config.LOOPBACK, port), timeout=CLIENT_TIMEOUT) as raw:
                raw.sendall(b"GET /api/probe HTTP/1.1\r\nHost: x\r\n\r\n")
                answer = raw.recv(4096)
        except OSError:
            answer = b""
    assert not answer.startswith(b"HTTP/"), "a plaintext request was answered by the TLS listener"


def test_the_listener_is_released_when_the_block_exits_normally(
    cfg: config.ServerConfig,
) -> None:
    with server.serve(cfg, [probe_route()]) as running:
        port = running.server_address[1]
    released = connect_refused(port)
    assert released is True, "the listener was still holding the port after a clean exit"


def test_the_listener_is_released_when_an_exception_leaves_the_block(
    cfg: config.ServerConfig,
) -> None:
    bound: list[int] = []

    def serve_then_raise() -> None:
        with server.serve(cfg, [probe_route()]) as running:
            bound.append(running.server_address[1])
            raise RuntimeError("deliberate")

    with pytest.raises(RuntimeError):
        serve_then_raise()
    listeners = len(bound)
    assert listeners == 1, "the block never bound, so the arm proves nothing about releasing it"
    released = connect_refused(bound[0])
    assert released is True, "an exception inside the block leaked the listening socket"


def test_the_listener_is_released_when_the_handler_itself_raises(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair

    def exploding(parameters: Mapping[str, str]) -> contract.Response:
        del parameters
        raise RuntimeError("deliberate")

    route = contract.Route(method="GET", template=PROBE_TEMPLATE, handler=exploding)
    port = EPHEMERAL
    with server.serve(cfg, [route]) as running:
        port = running.server_address[1]
        refusal = raw_get(port, cert, PROBE_TEMPLATE)[0]
    assert refusal != contract.HTTP_OK, "a raising handler answered 200"
    released = connect_refused(port)
    assert released is True


def test_the_sigint_handler_calls_shutdown_off_the_calling_thread() -> None:
    recorded: list[str] = []

    class Recorder:
        def shutdown(self) -> None:
            recorded.append(threading.current_thread().name)

    handler: Callable[[int, object], None] = server.shutdown_on_signal(Recorder())  # type: ignore[arg-type,assignment]
    caller = threading.current_thread().name
    handler(2, None)
    deadline = time.monotonic() + SETTLE_TIMEOUT
    while not recorded and time.monotonic() < deadline:
        time.sleep(0.01)
    calls = len(recorded)
    assert calls == 1, "the SIGINT handler did not reach shutdown"
    assert recorded[0] != caller, "shutdown ran on the signalled thread, which is the deadlock"


# ---------------------------------------------------------------------------
# (b) A bind failure never falls back
# ---------------------------------------------------------------------------


def test_a_bound_port_is_refused_rather_than_stolen(
    cert_pair: tuple[Path, Path], tmp_path: Path, occupied: int
) -> None:
    cert, key = cert_pair
    taken = config.ServerConfig(
        host=config.LOOPBACK,
        port=occupied,
        cert_path=cert,
        key_path=key,
        web_dir=tmp_path / "web",
    )
    entered = 0

    def enter_and_count() -> None:
        nonlocal entered
        with server.serve(taken, [probe_route()]):
            entered += 1

    with pytest.raises(server.BindError) as caught:
        enter_and_count()
    assert caught.value.port == occupied
    assert entered == 0, "the block was entered, so something was bound after all"


def test_the_bind_failure_names_the_port_and_the_two_places_to_look(
    cert_pair: tuple[Path, Path], tmp_path: Path, occupied: int
) -> None:
    cert, key = cert_pair
    taken = config.ServerConfig(
        host=config.LOOPBACK, port=occupied, cert_path=cert, key_path=key, web_dir=tmp_path
    )
    with pytest.raises(server.BindError) as caught:
        server.build_server(taken, [])
    message = str(caught.value)
    assert str(occupied) in message
    assert "config/ports.json" in message
    assert "scripts/verify_env.py" in message


def test_run_exits_non_zero_on_a_bind_failure_and_binds_nothing_else(
    cert_pair: tuple[Path, Path], tmp_path: Path, occupied: int
) -> None:
    cert, key = cert_pair
    taken = config.ServerConfig(
        host=config.LOOPBACK, port=occupied, cert_path=cert, key_path=key, web_dir=tmp_path
    )
    code = server.run(taken, [probe_route()])
    assert code != server.EXIT_OK
    assert code == server.EXIT_BIND_FAILED
    serving = sum(1 for name in sorted(t.name for t in threading.enumerate()) if "serve" in name)
    assert serving == 0, "a failed bind left a serving thread behind"


def test_an_unusable_certificate_is_a_distinct_non_zero_exit(tmp_path: Path) -> None:
    absent = config.ServerConfig(
        host=config.LOOPBACK,
        port=EPHEMERAL,
        cert_path=tmp_path / "nothing.cert.pem",
        key_path=tmp_path / "nothing.key.pem",
        web_dir=tmp_path / "web",
    )
    code = server.run(absent, [])
    assert code == server.EXIT_CERTIFICATE
    assert code != server.EXIT_BIND_FAILED


def test_an_unusable_certificate_message_names_no_path(tmp_path: Path) -> None:
    absent = config.ServerConfig(
        host=config.LOOPBACK,
        port=EPHEMERAL,
        cert_path=tmp_path / CANARY / "nothing.cert.pem",
        key_path=tmp_path / CANARY / "nothing.key.pem",
        web_dir=tmp_path / "web",
    )
    with pytest.raises(server.CertificateError) as caught:
        server.build_server(absent, [])
    leaked = str(caught.value).count(CANARY)
    assert leaked == 0, "the certificate refusal echoed a path that can sit under a home directory"


def test_the_server_refuses_any_address_that_is_not_loopback(
    cert_pair: tuple[Path, Path], tmp_path: Path
) -> None:
    cert, key = cert_pair
    wildcard = config.ServerConfig(
        host="0.0.0.0",  # noqa: S104
        port=EPHEMERAL,
        cert_path=cert,
        key_path=key,
        web_dir=tmp_path,
    )
    with pytest.raises(ValueError, match="binds"):
        server.build_server(wildcard, [])


# ---------------------------------------------------------------------------
# (b.1) A refusal reaching an operator renders a FIELD, never the object
# ---------------------------------------------------------------------------

#: The shipped module the two static arms below read.
SERVER_SOURCE: Final = SURFACE_ROOT / "server.py"

#: Builtins that turn an object into text. The same vocabulary
#: ``tests/test_exception_rendering.py`` sweeps the whole tree for, RESTATED
#: rather than imported: this arm exists so the repair is graded by something
#: inside CS-601 as well, and importing the guard's internals would make one
#: reading of the property wear two hats.
TEXT_BUILTINS: Final = frozenset({"ascii", "format", "repr", "str"})

#: How many sites the detector must find in :data:`LEAKY_RUN`.
LEAKY_RUN_SITES: Final = 2

#: How many ``raise CertificateError(...)`` sites the module has.
CERTIFICATE_RAISE_SITES: Final = 1

#: Tokens the bind refusal must carry on the channel an operator reads.
BIND_POINTERS: Final = 3

#: Ports the two spellings of the bind refusal are compared on. Chosen at both
#: ends of the transport's range and DELIBERATELY OUTSIDE THE ALLOCATED BAND:
#: ``config/ports.json`` owns the allocation and no other file restates it, which
#: ``test_config.py`` sweeps this whole package for. The first draft of this
#: constant pinned the band's low end and that sweep caught it.
BIND_PORTS: Final = (0, 1, 1024, 65535)

#: The PRE-REPAIR body of ``run``, authored here rather than read from history,
#: and the positive control for the detector below. ``str()`` on an ``OSError``
#: appends the path it failed on, so widening either handler by one word turns
#: this shape into a home-path leak - which is why the shape is refused
#: categorically rather than argued about per exception type.
LEAKY_RUN: Final = '''
def run(config, routes):
    """A body that renders the caught object at both of its handlers."""
    try:
        serve(config, routes)
    except CertificateError as exc:
        sys.stderr.write(f"{exc}\\n")
        return 3
    except BindError as exc:
        sys.stderr.write(f"{exc}\\n")
        return 4
    return 0
'''


def _object_renderings(node: ast.expr, bound: str) -> tuple[str, ...]:
    """Every way one expression renders the whole object ``bound`` names.

    Args:
        node: The expression to read. An ``ast.expr`` rather than an
            ``ast.AST``, because every rendering shape is an expression and
            only an expression is guaranteed to carry a line number.
        bound: The name an ``except ... as`` clause bound.

    Returns:
        One shape string per rendering, empty when this node renders nothing.
        Only a BARE name counts: ``exc.port`` is an attribute read of a named
        field, which is the repaired spelling and not a finding.
    """

    def is_bound(expr: ast.expr) -> bool:
        return isinstance(expr, ast.Name) and expr.id == bound

    if isinstance(node, ast.JoinedStr):
        return tuple(
            f"f-string {{{bound}}}"
            for part in node.values
            if isinstance(part, ast.FormattedValue) and is_bound(part.value)
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        right = node.right
        operands = right.elts if isinstance(right, ast.Tuple) else [right]
        return tuple(f"percent-format {bound}" for operand in operands if is_bound(operand))
    if isinstance(node, ast.Call):
        function = node.func
        if isinstance(function, ast.Name) and function.id in TEXT_BUILTINS:
            return tuple(f"{function.id}({bound})" for arg in node.args if is_bound(arg))
        if isinstance(function, ast.Attribute) and function.attr == "format":
            supplied = [*node.args, *(keyword.value for keyword in node.keywords)]
            return tuple(f".format({bound})" for arg in supplied if is_bound(arg))
    return ()


def _rendered_exception_objects(source: str, function: str) -> tuple[str, ...]:
    """Every place one module-level function renders a caught exception OBJECT.

    STATED LIMIT: a handler nested inside another handler is walked twice, so a
    rendering inside one would be counted twice. ``run`` has two flat handlers
    and the control below has the same two, so no count here depends on it.

    Args:
        source: The module text.
        function: The module-level function to read.

    Returns:
        ``<line>:<shape>`` for each rendering, sorted. Line numbers and shape
        words only - this text reaches a failure report.
    """
    tree = ast.parse(source)
    target = next(
        (node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == function),
        None,
    )
    assert target is not None, f"the source read declares no module-level {function}"
    found: list[str] = []
    for handler in ast.walk(target):
        if not isinstance(handler, ast.ExceptHandler) or handler.name is None:
            continue
        bound = handler.name
        for node in ast.walk(handler):
            if not isinstance(node, ast.expr):
                continue
            found.extend(f"{node.lineno}:{shape}" for shape in _object_renderings(node, bound))
    return tuple(sorted(found))


def test_the_object_rendering_detector_finds_the_shape_it_looks_for() -> None:
    """THE POSITIVE CONTROL, and the arm below proves nothing without it.

    A detector that resolves no name and a ``run`` that renders no object
    return the same empty tuple - byte-identical outcomes. This is the shape the
    repo-wide guard reported against this module, asserted to be FOUND.
    """
    found = len(_rendered_exception_objects(LEAKY_RUN, "run"))
    assert found == LEAKY_RUN_SITES, "the detector does not see the shape it exists to find"


def test_run_renders_no_caught_exception_object() -> None:
    """Neither refusal handler may render the object it caught.

    CATEGORICAL, AND DELIBERATELY NOT ARGUED PER TYPE. Both handlers catch a
    type this module declares, whose message is fixed text today - so there is
    no live leak at either site. The day one ``except`` clause is widened to
    ``OSError``, or one message is chained through, ``str()`` appends the path
    the call failed on and the account name reaches stderr. The rule protects
    against the change, not against the current state.
    """
    found = len(_rendered_exception_objects(SERVER_SOURCE.read_text(encoding="utf-8"), "run"))
    assert found == 0, (
        "run() renders a caught exception object; render a named FIELD or the "
        "module constant instead - see tests/test_exception_rendering.py"
    )


def test_every_certificate_refusal_is_raised_with_the_one_constant() -> None:
    """What makes it FAITHFUL for ``run`` to write the constant.

    Writing ``CERTIFICATE_UNUSABLE`` is the right line only while that is what
    every raise site passes. A second refusal built from a path would otherwise
    be silently replaced by the wrong text, which is a worse fault than the
    leak the replacement repaired.
    """
    tree = ast.parse(SERVER_SOURCE.read_text(encoding="utf-8"))
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise):
            continue
        raised = node.exc
        if (
            isinstance(raised, ast.Call)
            and isinstance(raised.func, ast.Name)
            and raised.func.id == "CertificateError"
        ):
            calls.append(raised)
    assert len(calls) == CERTIFICATE_RAISE_SITES, "the certificate raise sites moved"
    off_constant = sum(
        1
        for call in calls
        if not (
            len(call.args) == 1
            and isinstance(call.args[0], ast.Name)
            and call.args[0].id == "CERTIFICATE_UNUSABLE"
        )
    )
    assert off_constant == 0, (
        "a certificate refusal is built from something other than the module "
        "constant, so run() would write the wrong line for it"
    )


def test_the_bind_refusal_text_is_owned_by_the_module_not_by_the_exception() -> None:
    """The two spellings of one operator line cannot drift apart."""
    agree = sum(
        1 for port in BIND_PORTS if server.bind_refusal(port) == server.BindError(port).args[0]
    )
    assert agree == len(BIND_PORTS), (
        "the text run() writes and the text the raise site builds have diverged"
    )


def test_run_writes_the_certificate_refusal_verbatim_and_names_no_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    absent = config.ServerConfig(
        host=config.LOOPBACK,
        port=EPHEMERAL,
        cert_path=tmp_path / CANARY / "nothing.cert.pem",
        key_path=tmp_path / CANARY / "nothing.key.pem",
        web_dir=tmp_path / "web",
    )
    code = server.run(absent, [])
    written = capsys.readouterr().err
    assert code == server.EXIT_CERTIFICATE
    identical = written == f"{server.CERTIFICATE_UNUSABLE}\n"
    assert identical, "run() no longer writes the one certificate refusal this module owns"
    leaked = written.count(CANARY)
    assert leaked == 0, "the certificate refusal reached stderr carrying a path"


def test_run_writes_the_bind_refusal_the_raise_site_builds(
    cert_pair: tuple[Path, Path],
    tmp_path: Path,
    occupied: int,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cert, key = cert_pair
    taken = config.ServerConfig(
        host=config.LOOPBACK, port=occupied, cert_path=cert, key_path=key, web_dir=tmp_path
    )
    code = server.run(taken, [probe_route()])
    written = capsys.readouterr().err
    assert code == server.EXIT_BIND_FAILED
    identical = written == f"{server.bind_refusal(occupied)}\n"
    assert identical, "the bind refusal an operator reads is no longer the one that was raised"
    pointers = sum(
        1
        for token in (str(occupied), "config/ports.json", "scripts/verify_env.py")
        if token in written
    )
    assert pointers == BIND_POINTERS, (
        "the bind refusal lost the port or one of the two places to look, both "
        "of which are what makes it actionable"
    )


# ---------------------------------------------------------------------------
# (c) Traversal cannot resolve, because there is no resolution step
# ---------------------------------------------------------------------------

TRAVERSALS: Final = (
    "/../../work/x.sav",
    "/app.js/../x",
    "/../../anything",
    "/./app.js",
    "/app.js/",
    "/web/app.js",
    "/index.html",
    "/APP.CSS",
    "/app.js%2f..%2fx",
    "/..%2f..%2fwork",
    "/api/../app.js",
)


@pytest.mark.parametrize("path", TRAVERSALS)
def test_a_path_outside_the_frozen_table_is_404(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path], path: str
) -> None:
    cert, _key = cert_pair
    cfg.web_dir.mkdir(parents=True, exist_ok=True)
    (cfg.web_dir / "app.js").write_bytes(b"// asset")
    (cfg.web_dir / "index.html").write_bytes(b"<!doctype html>")
    assets = providers.StaticAssets(cfg.web_dir, server.ASSET_NAMES)
    with server.serve(cfg, [probe_route()], assets) as running:
        status, answer = raw_get(running.server_address[1], cert, path)
    assert status == contract.HTTP_NOT_FOUND
    assert contract.ENDPOINT_UNROUTED.encode("ascii") in answer


@pytest.mark.parametrize("path", TRAVERSALS)
def test_a_traversal_never_returns_the_bytes_of_a_real_asset(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path], path: str
) -> None:
    """The consequence arm. A 404 code with the file's bytes attached is not a refusal."""
    cert, _key = cert_pair
    cfg.web_dir.mkdir(parents=True, exist_ok=True)
    (cfg.web_dir / "app.js").write_bytes(b"// asset")
    (cfg.web_dir / "index.html").write_bytes(b"<!doctype html>")
    assets = providers.StaticAssets(cfg.web_dir, server.ASSET_NAMES)
    with server.serve(cfg, [probe_route()], assets) as running:
        _status, answer = raw_get(running.server_address[1], cert, path)
    served = answer.count(b"// asset") + answer.count(b"<!doctype html>")
    assert served == 0, "a path outside the frozen table was answered with asset bytes"


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("//app.js", contract.HTTP_OK),
        ("////app.js", contract.HTTP_OK),
        ("//web/app.js", contract.HTTP_NOT_FOUND),
        ("//../../work/x.sav", contract.HTTP_NOT_FOUND),
        ("//api/probe", contract.HTTP_OK),
    ],
)
def test_a_leading_double_slash_collapses_and_still_cannot_leave_the_table(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path], path: str, expected: int
) -> None:
    """A MEASURED stdlib normalisation, pinned rather than assumed.

    ``BaseHTTPRequestHandler.parse_request`` rewrites a path beginning ``//`` to
    a single leading slash before any code in this repository runs - CPython
    gh-87389, because clients read ``//path`` as a scheme-less absolute URI.
    ``//app.js`` therefore reaches routing as ``/app.js`` and is served, which is
    why it is NOT in the traversal list above: it is an alias for an
    allow-listed name, not an escape from the table. The arms that matter are
    the two 404s - collapsing the slashes still lands on exact matching against
    three authored names, so it reaches nothing the table does not already name.
    Pinned here because it is behaviour this layer inherits and does not own,
    and an upgrade that changed it should be visible.
    """
    cert, _key = cert_pair
    cfg.web_dir.mkdir(parents=True, exist_ok=True)
    (cfg.web_dir / "app.js").write_bytes(b"// asset")
    assets = providers.StaticAssets(cfg.web_dir, server.ASSET_NAMES)
    with server.serve(cfg, [probe_route()], assets) as running:
        status, _answer = raw_get(running.server_address[1], cert, path)
    assert status == expected


def test_a_404_never_reflects_the_path_that_was_asked_for(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    with server.serve(cfg, [probe_route()]) as running:
        status, _headers, body = request(running.server_address[1], f"/{CANARY}", cert)
    assert status == contract.HTTP_NOT_FOUND
    reflected = body.count(CANARY.encode("ascii"))
    assert reflected == 0, "the 404 body reflected caller-chosen text"


def test_a_known_template_with_the_wrong_method_is_405(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    with server.serve(cfg, [probe_route()]) as running:
        status, _headers, body = request(
            running.server_address[1], PROBE_TEMPLATE, cert, method="POST"
        )
    assert status == contract.HTTP_METHOD_NOT_ALLOWED
    assert PROBE_TEMPLATE.encode("ascii") in body


def test_a_static_path_with_the_wrong_method_is_405_naming_no_path(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    with server.serve(cfg, [probe_route()]) as running:
        status, _headers, body = request(running.server_address[1], "/app.js", cert, method="POST")
    assert status == contract.HTTP_METHOD_NOT_ALLOWED
    assert contract.ENDPOINT_UNROUTED.encode("ascii") in body


def test_a_repeated_query_parameter_is_refused_as_malformed(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    seen: list[Mapping[str, str]] = []
    with server.serve(cfg, [probe_route(seen)]) as running:
        status, _headers, body = request(
            running.server_address[1], f"{PROBE_TEMPLATE}?a=1&a=2", cert
        )
    assert status == contract.HTTP_BAD_REQUEST
    assert contract.REASON_MALFORMED_QUERY.encode("ascii") in body
    reached = len(seen)
    assert reached == 0, "an ambiguous query reached the handler instead of being refused"


def test_a_well_formed_query_reaches_the_handler_intact(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    seen: list[Mapping[str, str]] = []
    with server.serve(cfg, [probe_route(seen)]) as running:
        status, _headers, _body = request(
            running.server_address[1], f"{PROBE_TEMPLATE}?rate=12&item=iron", cert
        )
    assert status == contract.HTTP_OK
    calls = len(seen)
    assert calls == 1
    assert seen[0] == {"rate": "12", "item": "iron"}


# ---------------------------------------------------------------------------
# Route registration refuses what it cannot route
# ---------------------------------------------------------------------------


def test_routing_refuses_a_template_carrying_a_path_parameter() -> None:
    route = contract.Route(method="GET", template="/api/world/<token>", handler=lambda _p: None)  # type: ignore[arg-type,return-value]
    with pytest.raises(server.RouteError) as caught:
        server.routing([route])
    assert server.ROUTE_HAS_A_PATH_PARAMETER in str(caught.value)


def test_routing_refuses_a_template_that_is_not_a_template() -> None:
    route = contract.Route(method="GET", template="/app.js", handler=lambda _p: None)  # type: ignore[arg-type,return-value]
    with pytest.raises(server.RouteError) as caught:
        server.routing([route])
    assert server.ROUTE_NOT_A_TEMPLATE in str(caught.value)


def test_routing_refuses_an_unknown_method() -> None:
    route = contract.Route(method="get", template=PROBE_TEMPLATE, handler=lambda _p: None)  # type: ignore[arg-type,return-value]
    with pytest.raises(server.RouteError) as caught:
        server.routing([route])
    assert server.ROUTE_METHOD_UNKNOWN in str(caught.value)


def test_routing_refuses_two_routes_claiming_one_method_and_template() -> None:
    with pytest.raises(server.RouteError) as caught:
        server.routing([probe_route(), probe_route()])
    assert server.ROUTE_DUPLICATED in str(caught.value)


def test_a_route_refusal_never_quotes_the_offending_template() -> None:
    route = contract.Route(method="GET", template=f"/{CANARY}", handler=lambda _p: None)  # type: ignore[arg-type,return-value]
    with pytest.raises(server.RouteError) as caught:
        server.routing([route])
    leaked = str(caught.value).count(CANARY)
    assert leaked == 0


# ---------------------------------------------------------------------------
# (d) Headers and identity
# ---------------------------------------------------------------------------


def test_every_response_carries_the_fixed_header_set(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    with server.serve(cfg, [probe_route()]) as running:
        _status, headers, body = request(running.server_address[1], PROBE_TEMPLATE, cert)
    assert headers["cache-control"] == "no-store"
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["referrer-policy"] == "no-referrer"
    assert headers["content-type"] == "application/json"
    assert headers["content-length"] == str(len(body))


def test_a_refusal_carries_the_fixed_header_set_too(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    with server.serve(cfg, [probe_route()]) as running:
        _status, headers, _body = request(running.server_address[1], "/nowhere", cert)
    present = sum(1 for name in FIXED_HEADER_NAMES if name in headers)
    assert present == len(FIXED_HEADER_NAMES)


def test_the_server_header_does_not_disclose_the_interpreter_version(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    with server.serve(cfg, [probe_route()]) as running:
        _status, headers, _body = request(running.server_address[1], PROBE_TEMPLATE, cert)
    banner = headers.get("server", "")
    assert banner == server.SERVER_BANNER
    assert "Python" not in banner
    assert "BaseHTTP" not in banner


def test_the_html_asset_carries_the_content_security_policy(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    cfg.web_dir.mkdir(parents=True, exist_ok=True)
    (cfg.web_dir / "index.html").write_bytes(b"<!doctype html>")
    assets = providers.StaticAssets(cfg.web_dir, server.ASSET_NAMES)
    with server.serve(cfg, [probe_route()], assets) as running:
        status, headers, body = request(running.server_address[1], "/", cert)
    assert status == contract.HTTP_OK
    assert body == b"<!doctype html>"
    assert headers["content-security-policy"] == server.CONTENT_SECURITY_POLICY
    assert headers["content-type"].startswith("text/html")


def test_a_json_answer_does_not_carry_the_html_policy(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    with server.serve(cfg, [probe_route()]) as running:
        _status, headers, _body = request(running.server_address[1], PROBE_TEMPLATE, cert)
    assert "content-security-policy" not in headers


def test_a_missing_asset_directory_is_a_404_rather_than_a_crash(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    assets = providers.StaticAssets(cfg.web_dir, server.ASSET_NAMES)
    # Bound to a scalar first: `assert not cfg.web_dir.exists()` renders
    # `cfg.web_dir` in full when it fails, and a temporary directory path is a
    # home path. tests/test_assertion_rendering.py grades exactly this.
    directory_absent = not cfg.web_dir.exists()
    assert directory_absent is True, "the arm needs the asset directory absent to mean anything"
    with server.serve(cfg, [probe_route()], assets) as running:
        status, _headers, _body = request(running.server_address[1], "/", cert)
    assert status == contract.HTTP_NOT_FOUND


def test_no_asset_provider_at_all_is_a_404_rather_than_a_crash(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    with server.serve(cfg, [probe_route()], None) as running:
        status, _headers, _body = request(running.server_address[1], "/", cert)
    assert status == contract.HTTP_NOT_FOUND


def test_a_head_answer_carries_the_length_but_not_one_byte_of_body(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    """Graded on the SOCKET, because the client library hides this one.

    An earlier version asked ``http.client`` for the body and asserted it empty.
    That passed with the body-suppression DELETED - MEASURED - because
    ``HTTPResponse`` sets a HEAD response's length to zero and never reads the
    socket at all. The assertion was about the client library, not the server.
    """
    cert, _key = cert_pair
    with server.serve(cfg, [probe_route()]) as running:
        port = running.server_address[1]
        head = raw_head(port, cert, PROBE_TEMPLATE)
        _status, got = raw_get(port, cert, PROBE_TEMPLATE)
    head_headers, _mark, head_body = head.partition(b"\r\n\r\n")
    _get_headers, _sep, get_body = got.partition(b"\r\n\r\n")
    # The control: the same route over GET must actually carry a body, or
    # "HEAD carried nothing" is a statement about an endpoint that returns
    # nothing either way.
    carried = len(get_body)
    assert carried > 0, "the GET carried no body, so the HEAD comparison proves nothing"
    written = len(head_body)
    assert written == 0, "a HEAD answer carried a body"
    assert b"Content-Length: " in head_headers, "a HEAD answer omitted the length"


# ---------------------------------------------------------------------------
# (e) The log channel, with the negative control that makes it mean anything
# ---------------------------------------------------------------------------


def drive_canary_requests(port: int, cert: Path) -> None:
    """Send the four shapes that carry caller-chosen bytes into a log path.

    Args:
        port: The listening port.
        cert: The certificate to trust.
    """
    request(port, f"{PROBE_TEMPLATE}?token={CANARY}", cert)
    request(port, PROBE_TEMPLATE, cert, headers={"X-Probe": CANARY})
    request(port, f"/{CANARY}", cert)
    raw_over_tls(port, cert, f"GET /{CANARY} HTTP/9.9\r\nHost: x\r\n\r\n".encode("ascii"))
    raw_over_tls(port, cert, f"{CANARY} sideways\r\n\r\n".encode("ascii"))
    raw_over_tls(port, cert, f"GET /{CANARY}\r\n\r\n".encode("ascii"))


#: Request lines the stdlib answers through ``send_error``, which builds its
#: reason phrase from the request bytes. Each shape drives a DIFFERENT branch of
#: ``parse_request``: an unsupported version, an unknown method, a malformed
#: version token, and a line with too few words.
MALFORMED_LINES: Final = (
    "GET /{c} HTTP/9.9\r\nHost: x\r\n\r\n",
    "{c} /api/probe HTTP/1.1\r\nHost: x\r\n\r\n",
    "GET /api/probe HTTP/{c}\r\nHost: x\r\n\r\n",
    "{c} sideways\r\n\r\n",
)


def drive_malformed_requests(port: int, cert: Path) -> list[bytes]:
    """Send every malformed shape and collect what came BACK.

    Args:
        port: The listening port.
        cert: The certificate to trust.

    Returns:
        One raw answer per shape.
    """
    return [
        raw_over_tls(port, cert, line.format(c=CANARY).encode("ascii")) for line in MALFORMED_LINES
    ]


def test_no_request_content_reaches_a_response_BODY(  # noqa: N802
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    """THE ARM THIS SUITE WAS MISSING, added because a mutation survived.

    Replacing ``DashboardHandler.send_error`` with the stdlib's own - which
    interpolates ``"Bad request version (%r)"`` and ``"Unsupported method
    (%r)"`` from request bytes - passed all 85 arms. MEASURED, not supposed. The
    stderr sweep could not see it because ``send_error`` does not leak to a LOG:
    it puts the caller's bytes on the response STATUS LINE and in the response
    BODY, and every arm was reading the wrong stream. An override defended at
    length in the module docstring was graded by nothing at all.
    """
    cert, _key = cert_pair
    with server.serve(cfg, [probe_route()]) as running:
        answers = drive_malformed_requests(running.server_address[1], cert)
    delivered = len(answers)
    assert delivered == len(MALFORMED_LINES), "no malformed request reached the server"
    answered = sum(1 for answer in answers if answer.startswith(b"HTTP/"))
    assert answered > 0, "nothing came back at all, so the arm read no response body"
    leaked = sum(answer.count(CANARY.encode("ascii")) for answer in answers)
    assert leaked == 0, "a malformed request line was echoed into a response"


def test_the_response_body_sweep_finds_a_planted_leak(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    """The negative control for the arm above, and it is the stdlib's own code."""
    cert, _key = cert_pair

    class Echoing(server.DashboardHandler):
        def send_error(
            self, code: int, message: str | None = None, explain: str | None = None
        ) -> None:
            BaseHTTPRequestHandler.send_error(self, code, message, explain)

    with serving_handler(cfg, Echoing) as port:
        answers = drive_malformed_requests(port, cert)
    found = sum(answer.count(CANARY.encode("ascii")) for answer in answers)
    assert found > 0, "the body sweep cannot see a leak, so its zeroes prove nothing"


def test_no_request_content_of_any_shape_reaches_stderr(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    cert, _key = cert_pair
    with server.serve(cfg, [probe_route()]) as running:
        drive_canary_requests(running.server_address[1], cert)
    captured = capsys.readouterr()
    leaked = captured.err.count(CANARY) + captured.out.count(CANARY)
    assert leaked == 0, "request content reached a log stream"


def test_the_stderr_sweep_finds_a_planted_leak(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """The negative control. Without it, a broken sweep and a clean server agree."""
    cert, _key = cert_pair

    class Leaky(server.DashboardHandler):
        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            sys.stderr.write((format % args) + "\n")

    with serving_handler(cfg, Leaky) as port:
        drive_canary_requests(port, cert)
    captured = capsys.readouterr()
    found = captured.err.count(CANARY)
    assert found > 0, "the sweep cannot see a leak, so its zeroes prove nothing"


def test_the_log_line_this_server_does_write_names_the_template_and_the_status(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    cert, _key = cert_pair
    with server.serve(cfg, [probe_route()]) as running:
        request(running.server_address[1], f"{PROBE_TEMPLATE}?token={CANARY}", cert)
    written = capsys.readouterr().err
    assert f"GET {PROBE_TEMPLATE} {contract.HTTP_OK}" in written
    leaked = written.count(CANARY)
    assert leaked == 0


def test_an_unknown_method_is_logged_as_a_literal_and_never_echoed(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    cert, _key = cert_pair
    with server.serve(cfg, [probe_route()]) as running:
        raw_over_tls(
            running.server_address[1],
            cert,
            f"{CANARY} /api/probe HTTP/1.1\r\nHost: x\r\n\r\n".encode("ascii"),
        )
    written = capsys.readouterr().err
    leaked = written.count(CANARY)
    assert leaked == 0, "an unrecognised method was echoed into the log"


def test_a_handler_that_raises_logs_only_the_exception_type(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    cert, _key = cert_pair

    def exploding(parameters: Mapping[str, str]) -> contract.Response:
        del parameters
        raise RuntimeError(CANARY)

    route = contract.Route(method="GET", template=PROBE_TEMPLATE, handler=exploding)
    with (
        server.serve(cfg, [route]) as running,
        pytest.raises((http.client.HTTPException, OSError)),
    ):
        request(running.server_address[1], PROBE_TEMPLATE, cert)
    written = capsys.readouterr().err
    assert "RuntimeError" in written, "the exception type is the one thing that should be reported"
    leaked = written.count(CANARY)
    assert leaked == 0, "the exception message reached stderr"
    assert "Traceback" not in written, "handle_error printed a traceback"


#: The two stdlib sinks that write caller bytes to stderr by default.
LOG_SINKS: Final = ("log_error", "log_message")

#: How many of its own parameters the planted leaky sink reads - format and args.
PLANTED_SINK_READS: Final = 2


def sink_uses_its_arguments(method: ast.FunctionDef) -> int:
    """How many of a log sink's own parameters its body reads.

    Args:
        method: The overriding method.

    Returns:
        The count. Zero is the only passing answer - a sink that never reads its
        arguments cannot echo them, whichever stdlib call site fires.
    """
    names = {arg.arg for arg in method.args.args[1:]}
    if method.args.vararg is not None:
        names.add(method.args.vararg.arg)
    used = {node.id for node in ast.walk(method) if isinstance(node, ast.Name)}
    return len(names & used)


def test_both_stdlib_log_sinks_are_overridden_and_ignore_every_argument() -> None:
    """``log_error`` IS GRADED STRUCTURALLY, and this arm says so rather than pretending.

    Restoring ``log_error`` to the stdlib default survives every runtime arm in
    this module - MEASURED by mutation. That is not a hole in the sweep, it is a
    consequence of the design: nothing in this handler calls ``log_error``,
    because the one stdlib path that would (``send_error``) is itself overridden.
    The override is kept as defence in depth for the paths that remain -
    ``handle_one_request`` calls it on a connection timeout - and for the day
    ``send_error`` changes. What can honestly be graded is its SHAPE, so that is
    what is graded: the method exists on this class, and its body reads none of
    its own parameters. Claiming a runtime proof here would be the "plausible
    rather than honest" answer this project refuses.
    """
    tree = ast.parse(Path(server.__file__).read_text(encoding="ascii"))
    handler = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "DashboardHandler"
    )
    sinks = {
        node.name: node
        for node in handler.body
        if isinstance(node, ast.FunctionDef) and node.name in LOG_SINKS
    }
    assert sorted(sinks) == sorted(LOG_SINKS), "a stdlib log sink is not overridden at all"
    disclosing = sum(sink_uses_its_arguments(method) for method in sinks.values())
    assert disclosing == 0, "a log sink reads its own arguments, so it can still echo them"


def test_the_log_sink_detector_finds_a_planted_positive() -> None:
    planted = ast.parse(
        "def log_message(self, format, *args):\n    sys.stderr.write(format % args)\n"
    ).body[0]
    assert isinstance(planted, ast.FunctionDef)
    found = sink_uses_its_arguments(planted)
    assert found == PLANTED_SINK_READS, "the sink detector cannot see a sink reading its arguments"


# ---------------------------------------------------------------------------
# (e) The layer writes nothing and computes nothing
# ---------------------------------------------------------------------------


def test_no_module_in_the_surface_layer_writes_to_the_filesystem() -> None:
    modules = surface_modules()
    swept = len(modules)
    assert swept >= MIN_SURFACE_MODULES, "the write sweep found too few modules to be meaningful"
    offending = sum(1 for path in modules if writes_in(path.read_text(encoding="ascii")))
    assert offending == 0, "a module in clockspeed/surface/ mutates the filesystem"


def test_the_write_detector_finds_each_planted_positive() -> None:
    planted = (
        "from pathlib import Path\nPath('x').write_text('y')\n",
        "from pathlib import Path\nPath('x').write_bytes(b'y')\n",
        "import os\nos.remove('x')\n",
        "import os\nos.unlink('x')\n",
        "import shutil\nshutil.rmtree('x')\n",
        "import shutil\nshutil.copy2('a', 'b')\n",
        "open('x', 'w')\n",
        "open('x', 'a')\n",
        "from pathlib import Path\nPath('x').mkdir()\n",
    )
    caught = sum(1 for source in planted if writes_in(source))
    assert caught == len(planted), "the write detector misses a shape it claims to cover"


def test_the_write_detector_does_not_fire_on_a_socket_write_or_a_string_replace() -> None:
    benign = "self.wfile.write(body)\ntext.replace('a', 'b')\nopen('x')\nopen('x', 'rb')\n"
    found = len(writes_in(benign))
    assert found == 0, "the write detector has false positives and will be switched off"


def test_only_the_two_named_modules_read_the_filesystem() -> None:
    modules = surface_modules()
    swept = len(modules)
    assert swept >= MIN_SURFACE_MODULES
    readers = frozenset(path.name for path in modules if reads_in(path.read_text(encoding="ascii")))
    assert readers == READERS_ALLOWED, "the filesystem-read allow-list moved"


def test_no_module_in_the_endpoint_package_touches_the_filesystem() -> None:
    endpoints = sorted((SURFACE_ROOT / "api").rglob("*.py"))
    swept = len(endpoints)
    assert swept >= MIN_ENDPOINT_MODULES, "the endpoint sweep found too few modules"
    offending = sum(
        1
        for path in endpoints
        if reads_in(path.read_text(encoding="ascii")) or writes_in(path.read_text(encoding="ascii"))
    )
    assert offending == 0, "an endpoint module reached for the filesystem"


def test_the_read_detector_finds_each_planted_positive() -> None:
    planted = (
        "from pathlib import Path\nPath('x').read_bytes()\n",
        "from pathlib import Path\nPath('x').read_text()\n",
        "open('x')\n",
        "from pathlib import Path\nlist(Path('x').iterdir())\n",
        "from pathlib import Path\nlist(Path('x').glob('*'))\n",
    )
    caught = sum(1 for source in planted if reads_in(source))
    assert caught == len(planted)


def test_no_module_in_the_surface_layer_derives_a_quantity() -> None:
    modules = surface_modules()
    swept = len(modules)
    assert swept >= MIN_SURFACE_MODULES
    offending = sum(1 for path in modules if arithmetic_in(path.read_text(encoding="ascii")))
    assert offending == 0, "a module in clockspeed/surface/ computes; surface never computes"


def test_the_arithmetic_detector_finds_a_planted_positive() -> None:
    planted = ("total = count + 1\n", "share = amount / 2\n", "scaled = rate * 60\n")
    caught = sum(1 for source in planted if arithmetic_in(source))
    assert caught == len(planted)


def test_the_arithmetic_detector_spares_a_set_difference_and_a_path_join() -> None:
    benign = "leftover = required - offered\nwhole = directory / name\ncount = len(items)\n"
    found = len(arithmetic_in(benign))
    assert found == 0, "the arithmetic detector fails correct code and will be switched off"


def test_the_static_surface_is_exactly_three_names() -> None:
    entries = len(server.STATIC_ROUTES)
    assert entries == STATIC_SURFACE_SIZE
    assert sorted(server.ASSET_NAMES) == ["app.css", "app.js", "index.html"]


def test_address_reuse_is_off_because_windows_permits_a_hijack_with_it_on() -> None:
    assert server.DashboardServer.allow_reuse_address is False
    assert server.DashboardServer.allow_reuse_port is False
    assert server.DashboardServer.daemon_threads is True


# ---------------------------------------------------------------------------
# (f) Providers answer None rather than raising, on a machine with no game
# ---------------------------------------------------------------------------


def test_a_world_provider_with_no_save_answers_none() -> None:
    provider = providers.SaveWorldProvider(find_save=lambda _dir: None)
    assert provider.world() is None


def test_a_world_provider_whose_loader_refuses_answers_none() -> None:
    def refusing(_path: Path) -> object:
        raise SaveRefusalError

    provider = providers.SaveWorldProvider(
        find_save=lambda _dir: Path("nowhere.sav"),
        load=refusing,  # type: ignore[arg-type]
    )
    assert provider.world() is None


class SaveRefusalError(OSError):
    """Stands in for any refusal the save layer can raise."""


def test_a_world_provider_hands_up_whatever_the_loader_returned() -> None:
    sentinel = object()
    provider = providers.SaveWorldProvider(
        find_save=lambda _dir: Path("a.sav"),
        load=lambda _path: sentinel,  # type: ignore[arg-type,return-value]
    )
    assert provider.world() is sentinel


def test_a_world_provider_satisfies_the_published_protocol() -> None:
    assert isinstance(providers.SaveWorldProvider(), contract.WorldProvider)


def test_a_registry_provider_with_no_install_answers_none() -> None:
    provider = providers.InstalledRegistryProvider(find_install=lambda: (None, "not found"))
    assert provider.registry() is None


def test_a_registry_provider_whose_docs_will_not_read_answers_none(tmp_path: Path) -> None:
    def refusing(_path: Path) -> str:
        raise OSError

    provider = providers.InstalledRegistryProvider(
        find_install=lambda: (tmp_path, "test"), read_docs=refusing
    )
    assert provider.registry() is None


def test_a_registry_provider_whose_docs_will_not_parse_answers_none(tmp_path: Path) -> None:
    provider = providers.InstalledRegistryProvider(
        find_install=lambda: (tmp_path, "test"), read_docs=lambda _path: "not a docs document"
    )
    assert provider.registry() is None


def test_a_registry_provider_satisfies_the_published_protocol() -> None:
    assert isinstance(providers.InstalledRegistryProvider(), contract.RegistryProvider)


def test_the_asset_reader_refuses_a_name_outside_its_closed_set(tmp_path: Path) -> None:
    tmp_path.joinpath("secret.txt").write_bytes(b"content")
    reader = providers.StaticAssets(tmp_path, server.ASSET_NAMES)
    assert reader.asset("secret.txt") is None


def test_the_asset_reader_refuses_a_traversal_even_if_it_were_allow_listed(
    tmp_path: Path,
) -> None:
    web = tmp_path / "web"
    web.mkdir()
    (tmp_path / "secret.json").write_bytes(OUTSIDE_BYTES)

    def reached(name: str) -> bool:
        try:
            return (web / name).read_bytes() == OUTSIDE_BYTES
        except OSError:
            return False

    # THE POSITIVE CONTROL, and it is the whole reason this arm means anything.
    # The first version of this test handed the reader separator names and
    # asserted None. It passed with the separator gate DELETED - MEASURED by
    # mutation - because the traversal targets did not exist, so the read failed
    # for its own reasons and file ABSENCE was doing the work the gate got credit
    # for. Proving the escape resolves first is what makes the refusal below a
    # statement about the gate.
    escapes = sum(1 for name in SEPARATOR_NAMES if reached(name))
    assert escapes == len(SEPARATOR_NAMES), "the escape does not resolve, so the arm grades nothing"
    reader = providers.StaticAssets(web, SEPARATOR_NAMES)
    refused = sum(1 for name in SEPARATOR_NAMES if reader.asset(name) is None)
    assert refused == len(SEPARATOR_NAMES), "the separator gate let a real traversal through"


def test_the_asset_reader_returns_the_bytes_of_a_name_it_was_told_about(
    tmp_path: Path,
) -> None:
    tmp_path.joinpath("app.js").write_bytes(b"// asset")
    reader = providers.StaticAssets(tmp_path, server.ASSET_NAMES)
    assert reader.asset("app.js") == b"// asset"


def test_the_asset_reader_answers_none_for_a_missing_directory(tmp_path: Path) -> None:
    reader = providers.StaticAssets(tmp_path / "absent", server.ASSET_NAMES)
    assert reader.asset("app.js") is None
