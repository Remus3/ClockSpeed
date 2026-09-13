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
b.2 NEITHER REFUSAL CHAINS A CAUSE, AND BOTH STILL DIAGNOSE (CS-857). The
   traceback channel is read through the DEFAULT EXCEPTHOOK in a child process,
   because the subject is what an operator's terminal shows and only the
   interpreter's own hook answers that. Two arms assert one exception is
   rendered and no chaining sentence is printed; a third asserts the three
   certificate failure modes still render DIFFERENT refusals, because closing
   the channel by making every failure identical is a regression in a different
   direction. Both directions have controls: the marker is proved to be a string
   the redactor rewrites, and a failing read is proved to render its filename
   through the same reader - without which a closed channel and a blind sweep
   are the same green.
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
g. A TEMPLATE CARRYING A PATH PARAMETER REGISTERS AND MATCHES (CS-601 slice S9).
   This reverses what (c) originally said. ``routing`` refused such a template
   outright, so ``/api/advice/<id>/derivation`` and ``/api/advice/<id>/state``
   had no concrete URL in production and ``serve(config, ROUTES)`` raised before
   it reached a socket. The refusal's stated reason - "a captured segment would
   have nowhere to go" - was the part that turned out to be wrong: a capture is
   a string, and ``Handler`` already takes ``Mapping[str, str]``. The arms below
   pin where the capture goes, who wins when a query parameter carries the same
   name, and - the part that needed the most care - that ADMITTING CALLER-CHOSEN
   TEXT INTO HANDLER INPUT did not open a reflection path. (c) is NARROWED
   rather than repealed: there is still no path RESOLUTION step, no
   normalisation and no filesystem join. Matching splits on ``/`` and compares
   segments, so ``..`` is a card id like any other rather than a directory.

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
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.data import locate
from clockspeed.surface import config, providers, server
from clockspeed.surface.api import contract, pending, routes
from tests import chained_cause_guard

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping, Sequence

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

#: The route every (g) arm registers. Its SHAPE is deliberately the shape of the
#: two templates BOOTSTRAP.md section 7.1 spells with a parameter, so an arm
#: proving something here is proving it about the endpoints that motivated the
#: slice rather than about a shape only a test ever asks for.
CAPTURE_TEMPLATE: Final = "/api/advice/<id>/state"

#: The parameter name that template declares. The key a capture must arrive
#: under, and - because a query string may carry any key at all - the name a
#: caller can also try to spell for itself.
CAPTURE_NAME: Final = "id"

#: A concrete segment with nothing special about it, for the arms that grade
#: matching rather than leakage.
PLAIN_ID: Final = "probe"

#: The repository root, which the (b.2) child subprocess puts on its import
#: path. Named once so the layer path below and the child's path cannot drift.
REPO_ROOT: Final = Path(__file__).resolve().parents[2]

#: The shipped layer both static sweeps walk.
SURFACE_ROOT: Final = REPO_ROOT / "clockspeed" / "surface"

#: Modules outside ``api/`` allowed to name a filesystem read. Asserted as an
#: EQUALITY, not a subset: a module dropping off the list is as much a finding as
#: one joining it, because it means the read moved somewhere unmeasured.
READERS_ALLOWED: Final = frozenset({"config.py", "providers.py"})

#: How few modules make the sweeps meaningless. A sweep over an empty population
#: passes vacuously, so each asserts this floor before it iterates.
MIN_SURFACE_MODULES: Final = 5
MIN_ENDPOINT_MODULES: Final = 2

#: The whole static surface, as a count an arm asserts rather than a literal
#: buried inside one: the page, the sheet, the script and every panel module.
#: DERIVED FROM THE SERVER'S OWN TABLE rather than retyped, because a hand-kept
#: count in a second file is the drift this arm exists to catch - and a count
#: that has to be edited in two places when a panel is added is a count that
#: will be edited in one.
#:
#: THE NUMBER IS NO LONGER WRITTEN HERE, AND THAT IS A REPAIR RATHER THAN A
#: TRIM. This comment said "SEVEN SINCE CS-962", and it was already false before
#: this line was next read: CS-977's ``panel_map.js`` took the surface to eight
#: without touching the prose, because the constant beside it derives and the
#: sentence does not. CLAUDE.md section 4 names a hardcoded measurement in prose
#: as a lie with a timestamp on it, and a stale one sitting on top of a correct
#: derivation is the worst version - it reads as the authority.
STATIC_SURFACE_SIZE: Final = len(server.ASSET_NAMES)

#: Header names every answer carries, whatever its status.
FIXED_HEADER_NAMES: Final = ("cache-control", "x-content-type-options", "referrer-policy")

#: Names carrying a separator, handed to the asset reader's closed set ON
#: PURPOSE so the arm grades the SECOND gate rather than the allow-list. Every
#: one must name something that EXISTS when the arm runs, and the arm plants
#: whatever the running platform does not already resolve - see the arm for
#: what went wrong when they did not exist.
SEPARATOR_NAMES: Final = ("../secret.json", "..\\secret.json", "a/../../secret.json")

#: What the escape targets contain, so reaching one is distinguishable from
#: reading anything else.
OUTSIDE_BYTES: Final = b"OUTSIDE-THE-WEB-DIRECTORY"

#: One subject filename per token the asset gate declares, as
#: ``(label, token, subject)``. EACH SUBJECT CARRIES EXACTLY ONE TOKEN, and that
#: is the entire point. The three names in SEPARATOR_NAMES above each carry
#: ``..`` AND a separator, so any single surviving token still refuses all
#: three, and none of them carries a colon at all - which made every token in
#: the gate an EQUIVALENT MUTANT. MEASURED, with those three as the only
#: subjects: deleting any ONE of the four tokens left the suite green, and only
#: emptying the tuple outright was caught.
#:
#: THE COLON SUBJECT HAS TWO LETTERS BEFORE THE COLON DELIBERATELY, and the
#: reason is measured rather than assumed. ``a:secret.json`` is the sharper
#: attack - pathlib reads a single letter plus a colon as a DRIVE, so joining it
#: to the web directory yields ``a:secret.json`` and DISCARDS the web directory
#: entirely - but a drive-relative escape cannot be planted as a positive
#: control on a machine with no such drive, and an unplantable subject grades
#: nothing. ``ab:`` is not a drive, so it stays under the web directory while
#: still carrying the token: an NTFS alternate data stream here, an ordinary
#: filename on a platform where a colon is one.
TOKEN_SUBJECTS: Final = (
    ("forward-slash", "/", "sub/secret.json"),
    ("backslash", "\\", "sub\\secret.json"),
    ("dot-dot", "..", "..secret.json"),
    ("colon", ":", "ab:secret.json"),
)

#: What a per-token subject contains. DISTINCT FROM OUTSIDE_BYTES because most
#: of these subjects sit INSIDE the web directory: the per-token arm grades that
#: the name WOULD BE READ, not that it escapes, and a marker called OUTSIDE
#: would misname three of the four.
TOKEN_SUBJECT_BYTES: Final = b"TOKEN-SUBJECT-INSIDE-THE-WEB-DIRECTORY"


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


def capture_route(
    seen: list[Mapping[str, str]] | None = None,
    *,
    method: str = "GET",
    template: str = CAPTURE_TEMPLATE,
) -> contract.Route:
    """A route on a template carrying a path parameter, recording what reached it.

    Args:
        seen: A list to append each call's parameters to, or None.
        method: The verb the route answers, so an arm can ask for one it does
            not answer and grade the 405.
        template: The template to register, so an arm can register two.

    Returns:
        The route. The 200 body names the TEMPLATE, never a captured value -
        ``contract.ok`` would accept a value here and that is exactly the shape
        the reflection arms exist to prove nothing ships.
    """

    def handler(parameters: Mapping[str, str]) -> contract.Response:
        if seen is not None:
            seen.append(dict(parameters))
        return contract.ok(template, {"probe": True})

    return contract.Route(method=method, template=template, handler=handler)


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
    cfg: config.ServerConfig,
    handler_class: type[BaseHTTPRequestHandler],
    routes_to_serve: Sequence[contract.Route] | None = None,
) -> Iterator[int]:
    """Serve with a DELIBERATELY LEAKY handler, for the negative controls.

    ``serve`` hardwires the real handler - correctly, since the handler is not a
    caller's choice in production. A planted leak therefore has to stand the
    listener up by hand. The lifetime discipline mirrors ``serve`` exactly, so a
    control that fails does not also leak a port into the rest of the suite.

    Args:
        cfg: Supplies the certificate pair.
        handler_class: The handler to serve with.
        routes_to_serve: The table to register, or None for the probe route
            alone. A control that grades a CAPTURED segment needs a table
            holding a template that can capture one.

    Yields:
        The bound port.
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cfg.cert_path, cfg.key_path)
    registered = [probe_route()] if routes_to_serve is None else list(routes_to_serve)
    listener = server.DashboardServer(
        (config.LOOPBACK, EPHEMERAL), handler_class, server.routing(registered), None
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


#: CS-987 - WHY THE LEAK ORACLE BELOW TAKES A DIFFERENCE AND NOT A COUNT.
#:
#: This arm used to finish with a population question::
#:
#:     serving = sum(1 for ... in threading.enumerate() if "serve" in name)
#:     assert serving == 0
#:
#: ``threading.enumerate()`` is PROCESS-wide. Under ``-n auto`` one xdist worker
#: runs many modules in one process, and ``server.py`` names its serving thread
#: ``clockspeed-serve`` - so a SUCCESSFUL ``server.run`` anywhere in that worker
#: leaves a daemon whose name satisfies the filter for the rest of the process's
#: life. On 2026-09-12 that made this arm RED on gw3 at ``assert 1 == 0`` while
#: everything it is actually about BEHAVED: the bind failed as designed, the exit
#: was ``EXIT_BIND_FAILED``, and the refusal printed naming the port and
#: ``OSError 10048``. The arm had read a neighbour's residue as its own leak.
#:
#: THE FALSE RED WAS THE LESSER FAULT. A population question cannot tell the
#: subject's own leak from a neighbour's live thread in one direction, nor from a
#: neighbour's already-exited thread in the other - so on a run where no sibling
#: has served yet it reports 0 whether or not the subject leaked. It could not
#: observe the value it was asked about, which is the one way an arm passes for
#: no reason at all.
#:
#: SO THE SUBJECT IS ISOLATED BY IDENTITY, NOT BY NAME. The set of thread
#: identities is taken before and after the call and the assertion is on what
#: APPEARED. Identity rather than name because a name is not unique and a
#: neighbour may start another thread sharing one. Narrowing the FILTER instead -
#: excluding daemons, matching the name harder, or marking this arm serial -
#: would each have left the oracle asking a global question and merely reduced
#: the population able to answer it, which is why none of the three was taken.
def test_run_exits_non_zero_on_a_bind_failure_and_binds_nothing_else(
    cert_pair: tuple[Path, Path], tmp_path: Path, occupied: int
) -> None:
    cert, key = cert_pair
    taken = config.ServerConfig(
        host=config.LOOPBACK, port=occupied, cert_path=cert, key_path=key, web_dir=tmp_path
    )
    before = {t.ident for t in threading.enumerate()}
    code = server.run(taken, [probe_route()])
    assert code != server.EXIT_OK
    assert code == server.EXIT_BIND_FAILED
    appeared = sorted(
        t.name for t in threading.enumerate() if t.ident not in before and "serve" in t.name
    )
    left_behind = len(appeared)
    assert left_behind == 0, f"a failed bind left a serving thread behind: {appeared}"


def test_the_leak_oracle_ignores_a_serving_thread_this_call_did_not_start(
    cert_pair: tuple[Path, Path], tmp_path: Path, occupied: int
) -> None:
    """CS-987 - THE GREEN CONTROL, and it is the half that proves the repair.

    A foreign thread named exactly like the one the subject would leak is alive
    for this arm's whole duration. The arm above must stay GREEN through it,
    because that thread is not one the call under test created. Before the
    repair this is the shape that went red on a correct refusal.

    Without this control a difference-based oracle that still consulted the
    population would pass its own positive arm and nothing would say so.
    """
    cert, key = cert_pair
    taken = config.ServerConfig(
        host=config.LOOPBACK, port=occupied, cert_path=cert, key_path=key, web_dir=tmp_path
    )
    release = threading.Event()
    foreign = threading.Thread(target=release.wait, name="clockspeed-serve", daemon=True)
    foreign.start()
    try:
        assert foreign.is_alive(), "the control thread did not start, so this arm measures nothing"
        before = {t.ident for t in threading.enumerate()}
        assert foreign.ident in before, (
            "the control thread is not in the population it must survive"
        )
        code = server.run(taken, [probe_route()])
        appeared = sorted(
            t.name for t in threading.enumerate() if t.ident not in before and "serve" in t.name
        )
        left_behind = len(appeared)
        assert code == server.EXIT_BIND_FAILED
        assert left_behind == 0, f"the oracle counted a thread it did not start: {appeared}"
        naive = sum(1 for t in threading.enumerate() if "serve" in t.name)
        assert naive > 0, (
            "the NAIVE population oracle must still see the control, or this arm is not "
            "measuring the difference between the two questions"
        )
    finally:
        release.set()
        foreign.join(timeout=5)


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

#: The one function allowed to read :data:`server.CERTIFICATE_UNUSABLE`, and
#: how many reads of it are allowed anywhere else. Since CS-857 the raise site
#: passes a CAUSE rather than a message, so the refusal text has a single
#: author; a read outside it means the operator line grew a second one and can
#: drift. The count inside the owner is deliberately NOT pinned - it may spell
#: the constant once or twice - but it is asserted non-zero, so a module that
#: dropped the line entirely cannot satisfy the sweep by reading it nowhere.
CERTIFICATE_TEXT_OWNER: Final = "certificate_refusal"
CERTIFICATE_CONSTANT_READERS_OUTSIDE: Final = 0

#: Tokens the bind refusal must carry on the channel an operator reads.
BIND_POINTERS: Final = 3

#: Ports the two spellings of the bind refusal are compared on. Chosen at both
#: ends of the transport's range and DELIBERATELY OUTSIDE THE ALLOCATED BAND:
#: ``config/ports.json`` owns the allocation and no other file restates it, which
#: ``test_config.py`` sweeps this whole package for. The first draft of this
#: constant pinned the band's low end and that sweep caught it.
BIND_PORTS: Final = (0, 1, 1024, 65535)

#: How many cause spellings the drift sweep runs each port through: absent, and
#: present. Both, because a constructor that discarded the cause would agree
#: with the no-cause spelling on every port and be wrong on every real failure.
BIND_CAUSE_SPELLINGS: Final = 2

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


def test_every_certificate_refusal_carries_the_one_constant() -> None:
    """What makes it FAITHFUL for ``run`` to write the module's own line.

    Writing ``CERTIFICATE_UNUSABLE`` is the right line only while that is what
    every raise site produces. A second refusal built from a path would
    otherwise be silently replaced by the wrong text, which is a worse fault
    than the leak the replacement repaired.

    THE MECHANISM CHANGED WITH CS-857 AND THE PROPERTY DID NOT. This used to
    read the raise sites and assert each passed the constant positionally.
    ``CertificateError`` now takes a CAUSE and builds its own message through
    ``certificate_refusal``, so no raise site can pass text at all - the
    constant has exactly one reader in the module, which is a stronger
    guarantee than a per-site check. This asserts the two halves of that: the
    module names the constant once, and every refusal it can build carries it.
    """
    tree = ast.parse(SERVER_SOURCE.read_text(encoding="utf-8"))
    owner = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == CERTIFICATE_TEXT_OWNER
    )
    owned = frozenset(id(node) for node in ast.walk(owner))
    outside = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and node.id == "CERTIFICATE_UNUSABLE"
        and isinstance(node.ctx, ast.Load)
        and id(node) not in owned
    )
    assert outside == CERTIFICATE_CONSTANT_READERS_OUTSIDE, (
        "the certificate constant is read outside the one function that owns "
        "the refusal text, so two spellings of it can now drift"
    )
    inside = sum(
        1
        for node in ast.walk(owner)
        if isinstance(node, ast.Name)
        and node.id == "CERTIFICATE_UNUSABLE"
        and isinstance(node.ctx, ast.Load)
    )
    assert inside > 0, (
        "the owning function no longer reads the constant, so this sweep would "
        "pass against a module that had dropped the operator line entirely"
    )
    built = (server.certificate_refusal(), server.certificate_refusal("SomeError 1"))
    carried = sum(1 for text in built if server.CERTIFICATE_UNUSABLE in text)
    assert carried == len(built), (
        "a certificate refusal is built without the module constant, so run() "
        "would write the wrong line for it"
    )


def test_the_bind_refusal_text_is_owned_by_the_module_not_by_the_exception() -> None:
    """The two spellings of one operator line cannot drift apart.

    SWEPT WITH AND WITHOUT A CAUSE since CS-857. The cause is optional, so
    there are two texts per port rather than one, and a constructor that
    dropped the cause on the floor would agree with ``bind_refusal(port)`` on
    every port while rendering the wrong line for every real failure.
    """
    agree = sum(
        1
        for port in BIND_PORTS
        for cause in ("", "OSError 10048")
        if server.bind_refusal(port, cause) == server.BindError(port, cause).args[0]
    )
    assert agree == len(BIND_PORTS) * BIND_CAUSE_SPELLINGS, (
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
    identical = written == f"{server.certificate_refusal('FileNotFoundError 2')}\n"
    assert identical, "run() no longer writes the one certificate refusal this module owns"
    carries_constant = server.CERTIFICATE_UNUSABLE in written
    assert carries_constant, (
        "the line an operator reads lost the pointer at the minting script and "
        "the override variable, which is the only actionable half of it"
    )
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
    with pytest.raises(server.BindError) as caught:
        server.build_server(taken, [probe_route()])
    raised_cause = str(caught.value.cause_summary)
    code = server.run(taken, [probe_route()])
    written = capsys.readouterr().err
    assert code == server.EXIT_BIND_FAILED
    # THE CAUSE IS READ BACK FROM A REAL COLLISION RATHER THAN SPELLED HERE.
    # The socket error code is a platform's - 10048 on this one, 98 elsewhere -
    # so writing it into the arm would make it a Windows test. Comparing the
    # line an operator reads against the line the raise site built is the
    # property either way, and it now covers the cause as well as the port.
    identical = written == f"{server.bind_refusal(occupied, raised_cause)}\n"
    assert identical, "the bind refusal an operator reads is no longer the one that was raised"
    assert raised_cause, (
        "the bind refusal carried no cause summary, so an operator cannot tell "
        "a taken port from an address this host does not have"
    )
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
# (b.2) CS-857 - NEITHER REFUSAL CHAINS A CAUSE, AND BOTH STILL DIAGNOSE
#
# WHY THESE TWO SITES WERE CLOSED THOUGH NEITHER WAS MEASURED TO LEAK. Both
# were re-measured before this block was written, on five legs plus a control,
# and no leg rendered a path: ``load_cert_chain`` raises with ``filename`` unset
# on an absent file, a malformed PEM, an empty file and an unreadable one, and a
# bind collision raises an interpreter-generated address message. The control is
# the arm below, and it is what makes those absences readable: the SAME denied
# file through ``Path.read_bytes`` DOES set ``filename`` and DOES render the
# whole path, so a filename-bearing OSError here would have been seen.
#
# The reason to close them anyway is doctrine, stated in
# ``tests/chained_cause_guard.py``: ``MEASURED_LEAK`` is ordered BEFORE
# ``EXEMPT_RECORDED`` on purpose, so an exemption can never launder a measured
# leak - and the syntactic type leg reports both of these as one, because it
# resolves the handler clause to a builtin ``OSError`` subclass and cannot know
# whether the call it wraps attaches a filename. The stated cost of that
# ordering is that a genuinely-safe OSError site must be closed with
# ``from None`` rather than argued away. This is that closure.
#
# AND ``from None`` ALONE WOULD HAVE BEEN A REGRESSION IN THE OTHER DIRECTION.
# The wrapper messages are fixed constants that quote nothing by design, so
# suppressing the context with nothing put back leaves an operator unable to
# tell an absent pair from an unreadable one from one that does not parse. What
# is folded back in is TWO SCALARS THAT CANNOT SPELL A PATH - the cause's class
# name and its integer error code - which is the idiom
# ``clockspeed/save/world.py`` already states as ``WorldLoadError(stage,
# cause_type)`` and which ``handle_error`` above already uses. The code is in it
# because the class name ALONE is not enough at one of the two sites, MEASURED:
# a bind collision and an unavailable address are both plain ``OSError`` and are
# separated only by the code. The last arm holds that reason.
#
# THE CHANNEL IS READ THROUGH THE DEFAULT EXCEPTHOOK IN A CHILD PROCESS, not
# through ``traceback.format_exception``. The subject is what an operator's
# terminal shows when a refusal escapes, and only the interpreter's own hook
# answers that. The child's stderr NEVER leaves the reader below: it carries
# absolute frame paths, so it is reduced to counts and booleans before any
# assertion sees it (CLAUDE.md non-negotiable 12).
# ---------------------------------------------------------------------------

#: The needle every (b.2) leak sweep counts. It carries the ``.sav`` suffix so
#: it is a string ``clockspeed.data.locate.redact`` rewrites - which is the
#: property that makes counting it evidence about PERSONAL DATA rather than
#: about an arbitrary word. The first arm below proves the redactor rewrites it,
#: because a needle nothing treats as personal is a sweep about nothing.
CHAIN_MARKER: Final = "zqxchain857.sav"

#: The line the default excepthook opens each rendered exception with. Counting
#: these counts EXCEPTIONS RENDERED, which is the whole subject: two means a
#: cause was printed beside the wrapper, one means it was not.
TRACEBACK_HEADER: Final = "Traceback (most recent call last):"

#: The two sentences CPython prints BETWEEN a wrapper and something it chained.
#: Both are swept, not just the cause one: deleting ``from exc`` would silence
#: the first and open the second, which is the exact escape
#: ``tests/chained_cause_guard.py`` names as ``FORM_IMPLICIT``.
CHAIN_CONNECTORS: Final = (
    "The above exception was the direct cause of the following exception:",
    "During handling of the above exception, another exception occurred:",
)

#: How many exceptions a closed refusal renders: the wrapper, and nothing else.
LONE_EXCEPTION: Final = 1

#: A well-formed PEM envelope around unusable content, so the failure comes from
#: the parser rather than from the file being absent.
MALFORMED_PEM: Final = b"-----BEGIN CERTIFICATE-----\nnot base64\n-----END CERTIFICATE-----\n"

#: The three certificate failure modes an operator acts on DIFFERENTLY - mint or
#: repoint, fix permissions, re-mint a corrupt pair - as ``(label, plant)``. The
#: plant is what the arm does to the path before offering it.
CERTIFICATE_MODES: Final = ("absent", "malformed", "unreadable")

#: Two socket error codes that are the SAME CLASS and different failures:
#: "the port is taken" and "that address is not valid on this host". MEASURED
#: as the Windows spellings; the arm's claim is the class merging them, not the
#: numbers, and any two distinct codes carry it.
BIND_IN_USE: Final = 10048
BIND_UNAVAILABLE: Final = 10049

#: How long the child gets. A bound, so a wedged child is a failure rather than
#: a hung suite.
CHILD_TIMEOUT: Final = 120.0

#: The child that reproduces one refusal and lets the DEFAULT excepthook render
#: it. Nothing catches, deliberately: a caught refusal renders whatever the
#: catcher chooses, and the subject here is what the interpreter chooses.
CHAIN_CHILD_SOURCE: Final = '''"""Reproduce one refusal and let the default excepthook render it."""

import socket
import sys
from pathlib import Path

REPO = Path(sys.argv[1])
sys.path.insert(0, str(REPO))

from clockspeed.surface import config, server

LEG = sys.argv[2]
FIRST = Path(sys.argv[3])
SECOND = Path(sys.argv[4])


def configured(port):
    """The configuration for one leg."""
    return config.ServerConfig(
        host=config.LOOPBACK,
        port=port,
        cert_path=FIRST,
        key_path=SECOND,
        web_dir=REPO,
    )


if LEG == "control-read":
    FIRST.read_bytes()
elif LEG == "bind":
    HOLDER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    HOLDER.bind((config.LOOPBACK, 0))
    HOLDER.listen(1)
    server.build_server(configured(HOLDER.getsockname()[1]), ())
else:
    server.build_server(configured(0), ())
'''


@dataclass(frozen=True)
class ChildRendering:
    """What one child printed, reduced to scalars before anything asserts on it.

    THE RAW STDERR IS NEVER A FIELD. It carries an absolute frame path per
    stack level, so holding it would put one into every failure report this
    class reaches - the echo path CLAUDE.md non-negotiable 12 forbids, and the
    shape ``tests/test_assertion_rendering.py`` sweeps the tree for.

    Attributes:
        exit_code: The child's exit code. Non-zero is what proves the failure
            actually fired; a child that quietly succeeded renders no path for
            reasons having nothing to do with any repair.
        tracebacks: How many exceptions the excepthook rendered.
        connectors: How many chaining sentences it printed.
        marker_hits: How many times :data:`CHAIN_MARKER` appeared.
        wrapper_named: Whether the refusal class this leg should raise was
            named, so a child failing somewhere else is not read as a pass.
    """

    exit_code: int
    tracebacks: int
    connectors: int
    marker_hits: int
    wrapper_named: bool


def render_in_child(
    tmp_path: Path, leg: str, first: Path, second: Path, wrapper: str
) -> ChildRendering:
    """Run one leg in a child and reduce its stderr to counts.

    Args:
        tmp_path: Where the child script is written.
        leg: Which reproduction the child runs.
        first: The certificate path, or the file the control reads.
        second: The key path.
        wrapper: The class name the leg should end at.

    Returns:
        The reduced rendering. The stderr itself is discarded here and never
        returned, for the reason :class:`ChildRendering` states.
    """
    child = tmp_path / "chain_child.py"
    child.write_text(CHAIN_CHILD_SOURCE, encoding="utf-8")
    finished = subprocess.run(
        [sys.executable, str(child), str(REPO_ROOT), leg, str(first), str(second)],
        capture_output=True,
        text=True,
        timeout=CHILD_TIMEOUT,
        check=False,
    )
    written = finished.stderr
    return ChildRendering(
        exit_code=finished.returncode,
        tracebacks=written.count(TRACEBACK_HEADER),
        connectors=sum(written.count(sentence) for sentence in CHAIN_CONNECTORS),
        marker_hits=written.count(CHAIN_MARKER),
        wrapper_named=wrapper in written,
    )


def certificate_refusal_text(cert: Path, key: Path, tmp_path: Path) -> str:
    """The refusal message ``_tls_context`` builds for one pair.

    READ THROUGH ``pytest.raises`` RATHER THAN AN ``except ... as exc`` BLOCK,
    and that is not a style choice: ``str(exc)`` on a caught binding is the
    shape ``tests/test_exception_rendering.py`` forbids tree-wide. The value
    read back is the wrapper's OWN message, which this module authors.

    Args:
        cert: The certificate path to offer.
        key: The key path to offer.
        tmp_path: Supplies the unused asset directory.

    Returns:
        The refusal text the wrapper carries.
    """
    offered = config.ServerConfig(
        host=config.LOOPBACK, port=EPHEMERAL, cert_path=cert, key_path=key, web_dir=tmp_path
    )
    with pytest.raises(server.CertificateError) as caught:
        server.build_server(offered, [])
    return str(caught.value.args[0])


def certificate_mode_paths(tmp_path: Path) -> tuple[tuple[Path, Path], ...]:
    """One (cert, key) pair per mode in :data:`CERTIFICATE_MODES`.

    Args:
        tmp_path: Where the plants are made.

    Returns:
        The pairs, in the order the modes are declared.
    """
    absent = tmp_path / "absent.cert.pem"
    malformed = tmp_path / "malformed.cert.pem"
    malformed.write_bytes(MALFORMED_PEM)
    unreadable = tmp_path / "unreadable.cert.pem"
    unreadable.mkdir()
    return tuple((path, path) for path in (absent, malformed, unreadable))


def refusal_raise_sites() -> tuple[ast.Raise, ...]:
    """Every ``raise CertificateError(...)`` and ``raise BindError(...)``.

    Returns:
        The raise statements, in source order.
    """
    tree = ast.parse(SERVER_SOURCE.read_text(encoding="utf-8"))
    found: list[ast.Raise] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise):
            continue
        raised = node.exc
        if (
            isinstance(raised, ast.Call)
            and isinstance(raised.func, ast.Name)
            and raised.func.id in REFUSAL_CLASSES
        ):
            found.append(node)
    return tuple(found)


#: The two refusals this block grades, and how many raise sites the module has
#: for them. Asserted as an EQUALITY before anything iterates: a sweep over a
#: population that shrank to zero passes every absence below it.
REFUSAL_CLASSES: Final = frozenset({"BindError", "CertificateError"})
REFUSAL_RAISE_SITES: Final = 2

#: How the census spells this module. Its ``Site.module`` is a repo-relative
#: POSIX path from git, so it is written that way rather than derived from
#: :data:`SERVER_SOURCE`, whose separators are the platform's.
SERVER_MODULE: Final = "clockspeed/surface/server.py"


def test_the_chain_marker_is_a_needle_the_redactor_rewrites() -> None:
    """CONTROL. Counting a word nothing treats as personal proves nothing.

    Every leak sweep in this block counts :data:`CHAIN_MARKER` in a child's
    stderr. That count is evidence about PERSONAL DATA only while the marker is
    the kind of string this project redacts, so the redactor is asked first.
    """
    rewritten = locate.redact(f"/somewhere/deep/{CHAIN_MARKER}")
    survived = CHAIN_MARKER in rewritten
    assert not survived, (
        "the redactor left the marker intact, so counting it in a child's "
        "stderr says nothing about whether personal data would have been seen"
    )
    assert locate.SAVE_FILE_PLACEHOLDER in rewritten, (
        "the redactor rewrote the marker into something other than the save-file "
        "placeholder, so the needle is not the class of string it stands in for"
    )


def test_the_child_sweep_sees_a_path_when_one_is_actually_rendered(tmp_path: Path) -> None:
    """CONTROL, and every absence in this block is worthless without it.

    An absent marker also describes a child that never ran, never failed, or
    whose stderr was not read. This reads a failure that DOES render its
    filename - ``Path.read_bytes`` sets ``filename`` where ``load_cert_chain``
    leaves it None - through the same reader, so the instrument is proven to
    detect a path before it is used to report none.
    """
    subject = tmp_path / CHAIN_MARKER
    seen = render_in_child(tmp_path, "control-read", subject, subject, "FileNotFoundError")
    assert seen.exit_code != 0, (
        "the control child exited zero, so no failure was rendered at all and "
        "the absences below would be absences of nothing"
    )
    assert seen.wrapper_named, "the control child failed somewhere other than the read"
    assert seen.marker_hits > 0, (
        "a failing read did NOT render its filename through the default "
        "excepthook, so this reader cannot tell a closed channel from a blind one"
    )


def test_the_certificate_refusal_renders_no_chained_cause(tmp_path: Path) -> None:
    """The channel itself, at ``_tls_context``, through the default excepthook."""
    subject = tmp_path / CHAIN_MARKER
    seen = render_in_child(tmp_path, "cert-absent", subject, subject, "CertificateError")
    assert seen.exit_code != 0, "the child exited zero, so no refusal was rendered"
    assert seen.wrapper_named, "the child failed somewhere other than the certificate refusal"
    assert seen.connectors == 0, (
        "the certificate refusal printed a chaining sentence, so the cause it "
        "wrapped was rendered beside it"
    )
    assert seen.tracebacks == LONE_EXCEPTION, (
        "more than one exception reached the terminal, so a cause this module "
        "does not author was rendered with it"
    )
    assert seen.marker_hits == 0, "the certificate refusal rendered the path it failed on"


def test_the_bind_refusal_renders_no_chained_cause(
    cert_pair: tuple[Path, Path], tmp_path: Path
) -> None:
    """The channel itself, at ``build_server``, through the default excepthook.

    The child holds its own port so the collision is real and no port outside
    this test is touched.
    """
    cert, key = cert_pair
    seen = render_in_child(tmp_path, "bind", cert, key, "BindError")
    assert seen.exit_code != 0, "the child exited zero, so no refusal was rendered"
    assert seen.wrapper_named, "the child failed somewhere other than the bind refusal"
    assert seen.connectors == 0, (
        "the bind refusal printed a chaining sentence, so the OSError it wrapped "
        "was rendered beside it"
    )
    assert seen.tracebacks == LONE_EXCEPTION, (
        "more than one exception reached the terminal, so a cause this module "
        "does not author was rendered with it"
    )
    assert seen.marker_hits == 0, "the bind refusal rendered a path"


def test_both_refusal_raise_sites_are_cleared_by_the_census_that_owns_the_question() -> None:
    """``from None`` at both sites, GRADED BY THE OWNER RATHER THAN BY THIS MODULE.

    The runtime arms above grade the two legs a test can reach. This grades the
    FORM at every site, including one no leg exercises, which is what stops a
    third refusal from being added chained.

    IT ASKS THE CENSUS RATHER THAN READING ``ast.Raise.cause`` ITSELF, and that
    is not a convenience. ``tests/chained_exemption_guard.py`` holds that the
    tree has exactly ONE owner of "can a chained cause render" - the census,
    which answers by measurement - and that any other module touching the
    ``cause`` field statically is answering from a belief. An earlier draft of
    this arm did exactly that and was correctly reported. IMPORTING THE OWNER IS
    NOT WHAT CLEARS THIS ARM, and CS-888 is why: an import used to prove
    deferral outright, and it bought every importing module blanket module-wide
    immunity - most of them holding it unused, over a cause field they never
    read - so that clearance is abolished and the only routes out are being the
    owner or carrying a recorded reason. What
    keeps this arm out of the population is that it makes no static cause read
    AT ALL. Asking the census makes it STRONGER besides: it asserts the verdict
    the census actually publishes for these two sites, which is the thing
    CS-857's first conjunct is about, rather than a private re-derivation that
    could agree with the census while measuring something else.

    :data:`CLOSED_SUPPRESSED` is the census's ONE POSITIVE clearance, and it is
    structural - the interpreter sets ``__suppress_context__`` and the raise
    constructs a class the module itself declares. It is deliberately not
    ``unproven``, which would be an absence of evidence rather than a clearance.
    """
    graded = {
        site.key: chained_cause_guard.classify(site)
        for site in chained_cause_guard.raise_sites()
        if site.module == SERVER_MODULE
    }
    assert len(graded) == REFUSAL_RAISE_SITES, (
        "the census derives a different number of chained raises in the server "
        "module than this arm expects, so the two sites it grades have moved"
    )
    cleared = sum(
        1 for verdict in graded.values() if verdict == chained_cause_guard.CLOSED_SUPPRESSED
    )
    assert cleared == REFUSAL_RAISE_SITES, (
        "a refusal is not cleared by the census that owns the chaining question; "
        "write `from None` and fold what an operator needs into the wrapper as "
        f"named scalars instead. Verdicts this run: {sorted(graded.values())}"
    )


def test_every_refusal_raise_site_folds_a_measured_cause_back_in() -> None:
    """``from None`` without this would be a regression in the other direction.

    The cause argument is optional on both refusals, because
    ``tests/surface/test_routes.py`` constructs ``BindError`` with a port alone.
    That default must never be what a SHIPPED site relies on, so every raise
    site is asserted to pass a summary.
    """
    sites = refusal_raise_sites()
    assert len(sites) == REFUSAL_RAISE_SITES, "the refusal raise sites moved"
    summarised = 0
    for site in sites:
        raised = site.exc
        assert isinstance(raised, ast.Call)
        summarised += sum(
            1
            for argument in raised.args
            if isinstance(argument, ast.Call)
            and isinstance(argument.func, ast.Name)
            and argument.func.id == "cause_summary"
        )
    assert summarised == REFUSAL_RAISE_SITES, (
        "a refusal suppresses its context without folding the cause back in, so "
        "an operator cannot tell that failure mode from any other"
    )


def test_the_certificate_refusal_still_tells_its_failure_modes_apart(tmp_path: Path) -> None:
    """THE ANTI-REGRESSION ARM, and the reason ``from None`` alone was refused.

    Closing the channel by making every certificate failure render the same
    line is a regression in a different direction. These are the three modes an
    operator acts on differently: mint or repoint an absent pair, fix the
    permissions on an unreadable one, re-mint one that does not parse.
    """
    pairs = certificate_mode_paths(tmp_path)
    assert len(pairs) == len(CERTIFICATE_MODES), "a certificate failure mode lost its plant"
    refusals = tuple(certificate_refusal_text(cert, key, tmp_path) for cert, key in pairs)
    distinct = len(frozenset(refusals))
    assert distinct == len(CERTIFICATE_MODES), (
        "two of the three certificate failure modes render the SAME refusal, so "
        "suppressing the cause left an operator unable to tell them apart"
    )
    carried = sum(1 for text in refusals if server.CERTIFICATE_UNUSABLE in text)
    assert carried == len(CERTIFICATE_MODES), (
        "a certificate refusal no longer carries the one line this module owns"
    )


def test_no_certificate_refusal_names_a_path_on_any_failure_mode(tmp_path: Path) -> None:
    """What the wrapper gained must not be a path on ANY of the three modes."""
    planted = tmp_path / CANARY
    planted.mkdir()
    pairs = certificate_mode_paths(planted)
    leaked = sum(
        1 for cert, key in pairs if CANARY in certificate_refusal_text(cert, key, tmp_path)
    )
    assert leaked == 0, "a certificate refusal echoed a path that can sit under a home directory"


def test_a_cause_summary_separates_what_a_class_name_alone_merges() -> None:
    """WHY THE FOLD CARRIES THE CODE AND NOT THE CLASS NAME ALONE, measured.

    A bind collision and an unavailable address are BOTH plain ``OSError``, so
    a summary built from the class name would render them identically and the
    site would have been closed at the cost of the only distinction it had.
    """
    in_use = OSError(BIND_IN_USE, "the port is taken")
    unavailable = OSError(BIND_UNAVAILABLE, "the address is not valid here")
    merged_by_class = type(in_use).__name__ == type(unavailable).__name__
    assert merged_by_class, (
        "the two socket failures are no longer one class, so this arm no longer "
        "measures the reason the summary carries a code"
    )
    separated = server.cause_summary(in_use) != server.cause_summary(unavailable)
    assert separated, (
        "the cause summary renders two different socket failures identically, so "
        "an operator cannot tell a taken port from an address this host does not have"
    )


def test_a_cause_summary_renders_neither_a_path_nor_an_operating_system_message() -> None:
    """The summary is TWO SCALARS, and the arm names what is deliberately absent.

    ``strerror`` is left out on purpose: it is an operating-system message table
    of unbounded shape, and a bounded integer separates the same failures. A
    class name and an ``int`` are things this module can reason about
    categorically; a platform's message text is not.
    """
    carrying = OSError(
        BIND_IN_USE, f"an operating system message naming {CHAIN_MARKER}", CHAIN_MARKER
    )
    summary = server.cause_summary(carrying)
    assert CHAIN_MARKER not in summary, "the cause summary rendered a filename"
    assert "operating system message" not in summary, (
        "the cause summary rendered the operating system's message text, which "
        "is unbounded and is not what separates these failures"
    )
    assert type(carrying).__name__ in summary, "the cause summary dropped the class name"
    assert str(BIND_IN_USE) in summary, "the cause summary dropped the error code"


def test_a_cause_summary_survives_a_failure_carrying_no_code() -> None:
    """A cause with no ``errno`` is summarised by its class alone, not crashed on."""
    summary = server.cause_summary(ValueError("nothing numeric here"))
    assert summary == "ValueError", (
        "a cause carrying no error code did not fall back to its class name alone"
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


def test_routing_registers_a_template_carrying_a_path_parameter() -> None:
    """THE ARM THAT PINNED THE REFUSAL, REVERSED ON EVIDENCE RATHER THAN DELETED.

    What stood here asserted ``routing`` raises ``ROUTE_HAS_A_PATH_PARAMETER``.
    That refusal was a real decision and its stated reason was checkable: "a
    handler receives query parameters only, so a captured segment would have
    nowhere to go". The reason was wrong. ``contract.Handler`` is
    ``Callable[[Mapping[str, str]], Response]`` and a captured segment is a
    ``str``, so the mapping the signature already carries is somewhere for it to
    go. Four of the five surface components had meanwhile been built ASSUMING
    the capture works - ``contract.ENDPOINT_PATTERN`` admits ``<name>``,
    ``pending.py`` publishes both templates, ``health.py`` lists them in its
    liveness map and ``BOOTSTRAP.md`` section 7.1 specifies them - so the
    refusal, not the specification, was the outlier. Its consequence was that
    ``serve(config, ROUTES)`` raised before it reached a socket and two of the
    nine published endpoints had no reachable URL at all.

    The arm is REPLACED rather than removed because a behaviour whose arm simply
    vanishes is a behaviour nothing grades. This one now pins the reversal.
    """
    table = server.routing([capture_route()])
    registered = sorted(table)
    assert registered == [CAPTURE_TEMPLATE], "the template did not register under its own name"
    methods = sorted(table[CAPTURE_TEMPLATE])
    assert methods == ["GET"], "the template registered without the method it was given"


def test_routing_refuses_two_templates_that_would_match_one_request_path() -> None:
    """Ambiguity is refused at registration, where the alternative is silent.

    ``/api/advice/<id>/state`` and ``/api/advice/<card>/state`` match exactly the
    same set of paths. Nothing about a request can tell them apart, so which
    handler ran would fall out of registration order - the same
    "whichever iteration reached last" fault ``clockspeed/surface/api/routes.py``
    already refuses one layer up, and it is worse here because both templates
    would still be present and the table would still look the right size.
    """
    pair = [capture_route(), capture_route(template="/api/advice/<card>/state")]
    with pytest.raises(server.RouteError) as caught:
        server.routing(pair)
    assert server.ROUTE_AMBIGUOUS in str(caught.value)
    quoted = str(caught.value).count("advice")
    assert quoted == 0, "the ambiguity refusal quoted a template instead of naming the fault"


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
# (g) A template carrying a path parameter matches a concrete request path
#
# THE THREE DECISIONS THESE ARMS PIN, stated once here rather than repeated:
#
#   1. WHERE THE CAPTURE GOES. Into the same ``Mapping[str, str]`` the handler
#      already receives, under the parameter's own name. ``Handler`` is frozen
#      and was designed for QUERY parameters, but a capture is a string and the
#      signature admits it. A router that matched a template and then discarded
#      the segment it matched on would be its own kind of dishonesty, and the
#      advisor phase needs the id.
#   2. WHO WINS A NAME COLLISION. The PATH capture, always. It is structural -
#      it is part of which resource was addressed - and the query is not. A
#      query that could shadow a path capture is a request-smuggling shape:
#      ``/api/advice/abc/state?id=other`` would let the caller pick which card a
#      handler thought it was acting on.
#   3. THE CAPTURE IS CALLER-CHOSEN TEXT. This is the first of it admitted into
#      handler input anywhere in the surface layer, so the guarantee that it
#      goes no further is STRUCTURAL rather than a filter: ``_dispatch`` hands
#      the matched TEMPLATE - never the request path - to ``_log`` and to every
#      ``contract`` constructor it calls. There is deliberately NO charset
#      restriction on a capture beyond non-empty. A charset would be this
#      module inventing a card-id schema phase 5 has not written, and a template
#      that silently never matches a legitimate id is the fault this module's
#      own docstring names as worse than a refusal. What keeps a ``..`` capture
#      harmless is not a filter but the two static sweeps in (e): no module in
#      this layer outside ``config.py`` and ``providers.py`` reads the
#      filesystem at all, so there is nothing for a segment to traverse.
# ---------------------------------------------------------------------------


def test_a_concrete_path_reaches_the_handler_registered_under_its_template(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    seen: list[Mapping[str, str]] = []
    with server.serve(cfg, [capture_route(seen)]) as running:
        status, _headers, _body = request(
            running.server_address[1], f"/api/advice/{PLAIN_ID}/state", cert
        )
    assert status == contract.HTTP_OK
    calls = len(seen)
    assert calls == 1, "a concrete path did not reach the handler its template registered"
    assert seen[0] == {CAPTURE_NAME: PLAIN_ID}, "decision 1: the capture did not arrive by name"


def test_a_capture_joins_the_query_parameters_rather_than_replacing_them(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    seen: list[Mapping[str, str]] = []
    with server.serve(cfg, [capture_route(seen)]) as running:
        request(running.server_address[1], f"/api/advice/{PLAIN_ID}/state?rate=12&item=iron", cert)
    calls = len(seen)
    assert calls == 1
    assert seen[0] == {CAPTURE_NAME: PLAIN_ID, "rate": "12", "item": "iron"}


def test_a_query_parameter_cannot_shadow_a_path_capture_in_either_order(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    """DECISION 2, graded from both sides so it cannot be insertion-order luck.

    The canary is the QUERY value here, so "the path won" and "the canary is
    absent from what the handler saw" are the same statement, which is what lets
    both halves be asserted on scalars.
    """
    cert, _key = cert_pair
    seen: list[Mapping[str, str]] = []
    both_orders = 2
    with server.serve(cfg, [capture_route(seen)]) as running:
        port = running.server_address[1]
        request(port, f"/api/advice/{PLAIN_ID}/state?{CAPTURE_NAME}={CANARY}&other=1", cert)
        request(port, f"/api/advice/{PLAIN_ID}/state?other=1&{CAPTURE_NAME}={CANARY}", cert)
    calls = len(seen)
    assert calls == both_orders, "one of the two orders never reached the handler"
    won = sum(1 for parameters in seen if parameters.get(CAPTURE_NAME) == PLAIN_ID)
    assert won == both_orders, "a query parameter shadowed the path capture"
    shadowed = sum(1 for parameters in seen if CANARY in parameters.values())
    assert shadowed == 0, "the shadowing query value survived somewhere in the handler input"
    kept = sum(1 for parameters in seen if parameters.get("other") == "1")
    assert kept == both_orders, "resolving the collision discarded an unrelated query parameter"


def test_an_exact_template_wins_over_a_capture_that_would_also_match(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    """Literal precedence, decided rather than emergent.

    Both templates below can answer ``/api/advice/pinned/state``. The literal
    one wins, because it is the more specific statement of intent and because
    the alternative - falling out of dict iteration order - is a router whose
    behaviour depends on the order a caller happened to build a list in.
    """
    cert, _key = cert_pair
    literal = f"/api/advice/{PLAIN_ID}/state"
    exact_seen: list[Mapping[str, str]] = []
    capture_seen: list[Mapping[str, str]] = []
    table = [capture_route(capture_seen), capture_route(exact_seen, template=literal)]
    with server.serve(cfg, table) as running:
        status, _headers, _body = request(running.server_address[1], literal, cert)
    assert status == contract.HTTP_OK
    exact_calls = len(exact_seen)
    assert exact_calls == 1, "the literal template did not answer its own path"
    capture_calls = len(capture_seen)
    assert capture_calls == 0, "the parameterised template shadowed a literal one"


def test_an_empty_segment_does_not_satisfy_a_capture(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    """``/api/advice//state`` is 404, not a match with an empty id.

    The segment count lines up, so a matcher that only counted would route this.
    An empty capture is a card id no card has, and handing a handler ``{"id":
    ""}`` would make "the caller named nothing" indistinguishable from "the
    caller named a card". ``raw_get`` is used because ``http.client`` rewrites a
    doubled separator before it reaches the socket.
    """
    cert, _key = cert_pair
    seen: list[Mapping[str, str]] = []
    with server.serve(cfg, [capture_route(seen)]) as running:
        status, _raw = raw_get(running.server_address[1], cert, "/api/advice//state")
    assert status == contract.HTTP_NOT_FOUND
    reached = len(seen)
    assert reached == 0, "an empty segment was captured as an id"


def test_an_extra_segment_does_not_match_a_capture(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    """WHAT EXCLUDES THIS IS THE TRAILING LITERAL, NOT THE SEGMENT COUNT.

    MEASURED: deleting the length check from ``_captures`` left this arm green,
    because ``/api/advice/a/b/state`` still has to line ``b`` up against the
    literal ``state`` and fails there first. The arm is kept - the behaviour is
    required - but the mechanism it looks like it grades is graded by
    ``test_a_capture_in_the_last_segment_does_not_swallow_extra_segments``
    instead, on a template with no trailing literal to do the work.
    """
    cert, _key = cert_pair
    seen: list[Mapping[str, str]] = []
    with server.serve(cfg, [capture_route(seen)]) as running:
        status, _raw = raw_get(running.server_address[1], cert, "/api/advice/a/b/state")
    assert status == contract.HTTP_NOT_FOUND
    reached = len(seen)
    assert reached == 0, "a capture swallowed more than one segment"


def test_a_path_that_stops_short_of_the_template_does_not_match(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    """``/api/advice/probe`` is one of the paths the acceptance suite requires 404.

    Same measured caveat as the arm above: the trailing literal is what excludes
    it, so this pins the requirement rather than the length check.
    """
    cert, _key = cert_pair
    seen: list[Mapping[str, str]] = []
    with server.serve(cfg, [capture_route(seen)]) as running:
        status, _raw = raw_get(running.server_address[1], cert, f"/api/advice/{PLAIN_ID}")
    assert status == contract.HTTP_NOT_FOUND
    reached = len(seen)
    assert reached == 0


def test_a_capture_in_the_last_segment_does_not_swallow_extra_segments(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    """THE ARM THAT ACTUALLY GRADES THE SEGMENT COUNT, added because a mutant lived.

    ``/api/advice/<id>/state`` ends in a literal, so the two arms above are
    excluded by comparing ``state`` against something else and would pass with
    the length check deleted - MEASURED, not supposed. A template ending in its
    capture has no such literal, so this is the shape where the count is the
    only thing standing between one id and two segments joined into one.
    """
    cert, _key = cert_pair
    trailing = "/api/advice/<id>"
    seen: list[Mapping[str, str]] = []
    with server.serve(cfg, [capture_route(seen, template=trailing)]) as running:
        port = running.server_address[1]
        matched_status, _m = raw_get(port, cert, "/api/advice/one")
        extra_status, _e = raw_get(port, cert, "/api/advice/one/two")
        short_status, _s = raw_get(port, cert, "/api/advice")
    assert matched_status == contract.HTTP_OK, "a trailing capture did not match one segment"
    assert extra_status == contract.HTTP_NOT_FOUND, "a trailing capture swallowed two segments"
    assert short_status == contract.HTTP_NOT_FOUND, "a trailing capture matched a missing segment"
    calls = len(seen)
    assert calls == 1, "only the single-segment request should have reached the handler"
    assert seen[0] == {CAPTURE_NAME: "one"}


def test_a_traversal_shaped_capture_routes_without_resolving_anything(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    """``..`` is a card id, and this arm says so out loud rather than hiding it.

    ``/api/advice/../state`` MATCHES, and the handler is handed ``{"id": ".."}``.
    Nothing normalises it, nothing joins it to a directory and nothing reflects
    it - which is precisely (c) narrowed rather than repealed. Refusing ``..``
    here would look like a defence and would not be one: ``.`` and a
    percent-encoded spelling would both still arrive, and the property that
    actually holds is that this layer builds no filesystem path from a request
    at all, which (e) sweeps for statically.
    """
    cert, _key = cert_pair
    seen: list[Mapping[str, str]] = []
    with server.serve(cfg, [capture_route(seen)]) as running:
        status, _raw = raw_get(running.server_address[1], cert, "/api/advice/../state")
    assert status == contract.HTTP_OK
    calls = len(seen)
    assert calls == 1
    assert seen[0] == {CAPTURE_NAME: ".."}


def test_a_405_on_a_captured_route_names_the_template_and_not_the_path(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    with server.serve(cfg, [capture_route(method="POST")]) as running:
        status, _headers, body = request(
            running.server_address[1], f"/api/advice/{CANARY}/state", cert
        )
    assert status == contract.HTTP_METHOD_NOT_ALLOWED
    assert CAPTURE_TEMPLATE.encode("ascii") in body, "the 405 did not name the matched template"
    leaked = body.count(CANARY.encode("ascii"))
    assert leaked == 0, "the 405 body reflected the captured segment"


def test_a_malformed_query_on_a_captured_route_names_the_template_and_not_the_path(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    cert, _key = cert_pair
    with server.serve(cfg, [capture_route()]) as running:
        status, _headers, body = request(
            running.server_address[1], f"/api/advice/{CANARY}/state?a=1&a=2", cert
        )
    assert status == contract.HTTP_BAD_REQUEST
    assert contract.REASON_MALFORMED_QUERY.encode("ascii") in body
    assert CAPTURE_TEMPLATE.encode("ascii") in body, "the 400 did not name the matched template"
    leaked = body.count(CANARY.encode("ascii"))
    assert leaked == 0, "the 400 body reflected the captured segment"


def test_the_log_line_for_a_captured_route_names_the_template_not_the_path(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    cert, _key = cert_pair
    with server.serve(cfg, [capture_route()]) as running:
        request(running.server_address[1], f"/api/advice/{CANARY}/state", cert)
    written = capsys.readouterr().err
    assert f"GET {CAPTURE_TEMPLATE} {contract.HTTP_OK}" in written
    leaked = written.count(CANARY)
    assert leaked == 0, "the captured segment reached the log line"


#: Every branch a captured route can leave the dispatcher by, with the canary
#: planted in the segment the template captures. One shape would grade one
#: return; each of these names an endpoint of its own on the way out.
CAPTURE_CANARY_PATHS: Final = (
    "/api/advice/{c}/state",
    "/api/advice/{c}/state?rate=12",
    "/api/advice/{c}/state?id=shadow",
    "/api/advice/{c}/state?a=1&a=2",
)

#: Codes the sweep must have actually provoked. A sweep that found nothing
#: because every request 404ed would otherwise be green while grading nothing.
CAPTURE_BRANCH_CODES: Final = frozenset(
    {contract.HTTP_OK, contract.HTTP_BAD_REQUEST, contract.HTTP_METHOD_NOT_ALLOWED}
)


def drive_capture_canary_requests(port: int, cert: Path) -> list[tuple[int, bytes]]:
    """Ask for every captured-route shape, byte for byte, and keep what came back.

    Args:
        port: The listening port.
        cert: The certificate to trust.

    Returns:
        One (status, whole raw answer) per shape. The RAW answer, so the status
        line and the headers are swept as well as the body - the stdlib's own
        leak put caller bytes on the status line, not in the body.
    """
    return [raw_get(port, cert, path.format(c=CANARY)) for path in CAPTURE_CANARY_PATHS]


def sweep_both_method_tables(cfg: config.ServerConfig, cert: Path) -> list[tuple[int, bytes]]:
    """Drive the canary shapes against a table that answers GET and one that does not.

    Two servings rather than one, because the method check runs BEFORE the query
    parse: a GET-answering table can never reach the 405 return, and a
    POST-only table can never reach the 400 or the 200.

    Args:
        cfg: The listener configuration.
        cert: The certificate to trust.

    Returns:
        Every (status, raw answer) from both servings.
    """
    answers: list[tuple[int, bytes]] = []
    with server.serve(cfg, [capture_route()]) as running:
        answers += drive_capture_canary_requests(running.server_address[1], cert)
    with server.serve(cfg, [capture_route(method="POST")]) as running:
        answers += drive_capture_canary_requests(running.server_address[1], cert)
    return answers


def test_a_captured_segment_never_reaches_a_response_body(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    """DECISION 3, on the channel that is not a log.

    A captured segment is the first caller-chosen text this layer puts into
    handler input. The five advice endpoints read it not at all and return 501,
    so the correct answer is zero reflection - but "the code does not use it" is
    an argument, and the module docstring's account of ``send_error`` is the
    standing proof in this repository that an argument about an unreflected
    value can be wrong on a channel nobody was reading.
    """
    cert, _key = cert_pair
    answers = sweep_both_method_tables(cfg, cert)
    delivered = len(answers)
    expected = len(CAPTURE_CANARY_PATHS) * 2
    assert delivered == expected, "a canary request was never sent"
    answered = sum(1 for status, _raw in answers if status != 0)
    assert answered == delivered, "a request produced no HTTP answer, so its bytes were not swept"
    provoked = frozenset(status for status, _raw in answers)
    unreached = len(CAPTURE_BRANCH_CODES - provoked)
    assert unreached == 0, "the sweep never reached the branches it claims to"
    leaked = sum(raw.count(CANARY.encode("ascii")) for _status, raw in answers)
    assert leaked == 0, "a captured path segment was reflected into a response"


def test_the_captured_segment_body_sweep_finds_a_planted_reflection(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    """The negative control. A handler that really does echo its capture.

    Nothing is faked: the real ``serve``, the real matcher, the real encoder and
    the real client. The only planted thing is a handler that puts the value it
    was handed into the body it returns - which is exactly what a phase 5
    handler will be tempted to do, and exactly what this sweep has to be able to
    see.
    """
    cert, _key = cert_pair

    def reflecting(parameters: Mapping[str, str]) -> contract.Response:
        return contract.ok(CAPTURE_TEMPLATE, {"echo": parameters[CAPTURE_NAME]})

    route = contract.Route(method="GET", template=CAPTURE_TEMPLATE, handler=reflecting)
    with server.serve(cfg, [route]) as running:
        answers = drive_capture_canary_requests(running.server_address[1], cert)
    found = sum(raw.count(CANARY.encode("ascii")) for _status, raw in answers)
    assert found > 0, "the body sweep cannot see a reflected capture, so its zeroes prove nothing"


def test_a_captured_segment_never_reaches_stderr(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """DECISION 3, on the log channel."""
    cert, _key = cert_pair
    answers = sweep_both_method_tables(cfg, cert)
    captured = capsys.readouterr()
    delivered = len(answers)
    expected = len(CAPTURE_CANARY_PATHS) * 2
    assert delivered == expected, "a canary request was never sent"
    leaked = captured.err.count(CANARY) + captured.out.count(CANARY)
    assert leaked == 0, "a captured path segment reached a log stream"


def test_the_captured_segment_stderr_sweep_finds_a_planted_leak(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """The negative control, planted at the exact site the design depends on.

    ``_dispatch`` hands ``_log`` the matched TEMPLATE. Handing it ``self.path``
    instead is a one-word change and is the whole failure mode this decision
    guards, so that is what is planted.
    """
    cert, _key = cert_pair

    class LoggingTheRequestPath(server.DashboardHandler):
        def _log(self, template: str, code: int) -> None:
            del template
            sys.stderr.write(f"{self.path} {code}\n")

    with serving_handler(cfg, LoggingTheRequestPath, [capture_route()]) as port:
        drive_capture_canary_requests(port, cert)
    found = capsys.readouterr().err.count(CANARY)
    assert found > 0, "the stderr sweep cannot see a logged path, so its zeroes prove nothing"


def test_the_assembled_route_table_registers_every_template_it_publishes() -> None:
    """``serve(config, ROUTES)`` reaches ``routing`` before it reaches a socket.

    While the refusal stood, this raised and every acceptance arm downstream of
    the listener fixture reported a listener failure rather than the thing it
    graded.
    """
    table = server.routing(routes.ROUTES)
    assert sorted(table) == sorted({route.template for route in routes.ROUTES})


def test_both_path_parameter_endpoints_answer_over_a_real_request(
    cfg: config.ServerConfig, cert_pair: tuple[Path, Path]
) -> None:
    """The two endpoints that had no reachable URL, driven over TLS.

    The derivation route is 501 and NAMES its blocking item. The state route
    answers POST, so a GET on it is 405 and not 501 and not 404 - the resource
    is real, the verb is not, and that distinction is the one
    ``clockspeed/surface/api/pending.py`` is built around.
    """
    cert, _key = cert_pair
    with server.serve(cfg, routes.ROUTES) as running:
        port = running.server_address[1]
        derivation_code, _dh, derivation_body = request(
            port, f"/api/advice/{CANARY}/derivation", cert
        )
        state_code, _sh, state_body = request(port, f"/api/advice/{CANARY}/state", cert)
    assert derivation_code == contract.HTTP_NOT_IMPLEMENTED
    assert pending.PENDING_BLOCKER.encode("ascii") in derivation_body
    assert state_code == contract.HTTP_METHOD_NOT_ALLOWED
    leaked = derivation_body.count(CANARY.encode("ascii")) + state_body.count(
        CANARY.encode("ascii")
    )
    assert leaked == 0, "a shipped endpoint reflected the captured segment"


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


def test_the_static_surface_is_exactly_the_names_the_page_loads() -> None:
    """Prove the served set is the panel set, and neither has drifted.

    RENAMED AND WIDENED BY CS-962. It asserted exactly three names, so adding a
    panel module reddened it unconditionally - and it sits in a file no panel
    slice had on its write-list, which is how a decomposition that proved its
    own disjointness still collided. The count now derives from the server's
    own table; the NAMES are still spelled out, because that is the half that
    catches a module served by accident.
    """
    entries = len(server.STATIC_ROUTES)
    assert entries == STATIC_SURFACE_SIZE
    assert sorted(server.ASSET_NAMES) == [
        "app.css",
        "app.js",
        "index.html",
        "panel_map.js",
        "panel_optimize.js",
        "panel_power.js",
        "panel_registry.js",
        "panel_scope.js",
        "panel_solve.js",
        "panel_warnings.js",
    ]


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
    # The directory the third spelling walks through. Creating it for real makes
    # that spelling resolve component by component on a filesystem that checks
    # each one before stepping past it, instead of by the lexical ".." collapse
    # that happens to serve it on Windows.
    (web / "a").mkdir()

    def reached(name: str) -> bool:
        try:
            return (web / name).read_bytes() == OUTSIDE_BYTES
        except OSError:
            return False

    # Plant a real target for any spelling this platform does not already
    # resolve, measured rather than branched on the platform name. Where a
    # backslash is an ordinary filename character this creates the literal file
    # "..\secret.json" inside web/; where it is a separator there is nothing
    # left to do.
    for name in SEPARATOR_NAMES:
        if not reached(name):
            # SUPPRESSED, AND THE POSITIVE CONTROL BELOW IS THE REASON. A target
            # this platform will not carry has to REACH that assertion and be
            # reported as "the target does not resolve, so the arm grades
            # nothing". An unhandled OSError raised from inside this loop would
            # kill the arm with a message about a filesystem call instead, which
            # says nothing about whether the gate holds.
            with suppress(OSError, ValueError):
                (web / name).write_bytes(OUTSIDE_BYTES)

    # THE POSITIVE CONTROL, and it is the whole reason this arm means anything.
    # The first version of this test handed the reader separator names and
    # asserted None. It passed with the separator gate DELETED - MEASURED by
    # mutation - because the traversal targets did not exist, so the read failed
    # for its own reasons and file ABSENCE was doing the work the gate got credit
    # for. Proving every name reads first is what makes the refusals below
    # statements about the gate.
    #
    # The control does NOT claim every spelling escapes web/. On a filesystem
    # where a backslash is NOT a separator, "..\secret.json" is one ordinary
    # filename that never leaves the directory. It claims the thing the gate is
    # actually graded on, which holds either way: every one of these names WOULD
    # BE READ if the gate did not refuse it, so no refusal below is free.
    reachable = sum(1 for name in SEPARATOR_NAMES if reached(name))
    assert reachable == len(SEPARATOR_NAMES), (
        "the target does not resolve, so the arm grades nothing"
    )
    reader = providers.StaticAssets(web, SEPARATOR_NAMES)
    refused = sum(1 for name in SEPARATOR_NAMES if reader.asset(name) is None)
    assert refused == len(SEPARATOR_NAMES), "the separator gate let a real traversal through"


# ---------------------------------------------------------------------------
# The same gate, graded ONE TOKEN AT A TIME. The arm above grades the gate as a
# whole and cannot do better: its three names share their tokens, so it stays
# green with three of the four deleted. See TOKEN_SUBJECTS for the measurement.
# ---------------------------------------------------------------------------


def _reads_back(target: Path) -> bool:
    """Whether ``target`` reads the planted marker back on this platform.

    Args:
        target: The path a subject name joins to under the web directory.

    Returns:
        True when the bytes read are exactly the marker. Absent, unreadable, and
        "this filesystem rejects the name outright" all collapse to one False,
        because the only question asked is whether the read WOULD succeed - and
        this is the same read ``StaticAssets.asset`` performs.
    """
    try:
        return target.read_bytes() == TOKEN_SUBJECT_BYTES
    except (OSError, ValueError):
        return False


def _token_subject_is_readable(web: Path, subject: str) -> bool:
    """Plant one per-token subject under ``web`` and MEASURE whether it reads.

    THE CAPABILITY IS PROVEN RATHER THAN INFERRED FROM A PLATFORM NAME, for the
    reason ``tests/test_make_cert.py`` states at ``_posix_mode_bits_are_honoured``:
    branching on ``os.name`` freezes today's answer into the suite, and it is
    then wrong in both directions the moment either platform moves. What a
    subject needs genuinely differs between them - the backslash-spelled subject
    is a path through a subdirectory where a backslash is a separator and one
    ordinary filename where it is not, and the colon-spelled one is an alternate
    data stream on NTFS and an ordinary filename where a colon is an ordinary
    character.

    Args:
        web: The directory the reader under test is wired to. Its ``sub``
            subdirectory must already exist, since two subjects resolve through
            it wherever their token is a real separator.
        subject: The subject filename, carrying exactly one forbidden token.

    Returns:
        True when the subject reads back, so refusing it below is not free.
        False when this platform will not carry it at all, which the caller
        turns into a loud per-token skip rather than a silent pass.
    """
    target = web / subject
    if _reads_back(target):
        return True
    # SUPPRESSED FOR THE REASON THE ARM ABOVE SUPPRESSES ITS OWN PLANT: a name
    # this filesystem refuses is a subject that does not exist here, which is a
    # skip carrying a stated reason, not an OSError raised out of a helper.
    with suppress(OSError, ValueError):
        target.write_bytes(TOKEN_SUBJECT_BYTES)
    return _reads_back(target)


def test_every_token_the_asset_gate_declares_has_a_subject_that_grades_it() -> None:
    graded = tuple(sorted(token for _label, token, _subject in TOKEN_SUBJECTS))
    declared = tuple(sorted(providers.FORBIDDEN_IN_AN_ASSET_NAME))
    # ASSERTED ON THE COLLECTION RATHER THAN ON A SCALAR COUNT, and this is the
    # one place in this module where that is right: the rendered value is a
    # table of punctuation literals with no path and nothing personal in it, and
    # WHICH token diverged is the whole finding - a count would say only that
    # one did.
    #
    # This arm is also what keeps a token graded on a filesystem that cannot
    # carry its subject. The behavioural arm below skips there; membership of
    # the gate's own tuple is pure string work and is checked everywhere.
    assert graded == declared, (
        "the gate's declared tokens and the tokens graded below have diverged, "
        "so a token is enforced but ungraded, or graded but no longer enforced"
    )


@pytest.mark.parametrize(
    ("token", "subject"),
    [pytest.param(token, subject, id=label) for label, token, subject in TOKEN_SUBJECTS],
)
def test_the_asset_reader_refuses_each_forbidden_token_on_its_own(
    token: str, subject: str, tmp_path: Path
) -> None:
    web = tmp_path / "web"
    web.mkdir()
    # Two subjects resolve THROUGH this directory wherever their token is a real
    # separator, and neither needs it where it is not.
    (web / "sub").mkdir()

    # THE SUBJECT CARRIES ITS OWN TOKEN AND NO OTHER, checked here rather than
    # trusted from the table. Grading a name that carries two tokens is exactly
    # the defect this arm exists to repair, so editing the table must not be
    # able to reintroduce it quietly.
    assert token in subject, f"the {token!r} subject does not carry {token!r} at all"
    intruders = sum(
        1 for _label, other, _subject in TOKEN_SUBJECTS if other != token and other in subject
    )
    assert intruders == 0, (
        f"the {token!r} subject carries {intruders} other forbidden token(s), so "
        f"refusing it would not prove {token!r} itself is enforced"
    )

    # THE POSITIVE CONTROL, PER TOKEN. The arm above records what happens
    # without one: its first version passed with the gate DELETED, because the
    # targets did not exist and file ABSENCE was doing the work the gate got
    # credit for. The claim here is NOT that this subject escapes the web
    # directory - three of the four do not - but that it WOULD BE READ if the
    # gate did not refuse it, which is the property the gate is graded on.
    if not _token_subject_is_readable(web, subject):
        pytest.skip(
            f"this platform will not carry {subject!r}, the only subject here "
            f"that isolates {token!r}, so there is nothing for the gate to be "
            f"right or wrong about and a green result would be a statement "
            f"about nothing. The {token!r} token is UNMEASURED on this platform "
            f"rather than absent, and its membership of the gate is still "
            f"graded everywhere by the arm above"
        )

    # ALLOW-LISTED ON PURPOSE, so the refusal below comes from the token gate
    # and not from the closed-set check that precedes it.
    reader = providers.StaticAssets(web, [subject])
    assert reader.asset(subject) is None, (
        f"the asset gate served {subject!r}, so the {token!r} token is not enforced"
    )


def test_the_asset_reader_returns_the_bytes_of_a_name_it_was_told_about(
    tmp_path: Path,
) -> None:
    tmp_path.joinpath("app.js").write_bytes(b"// asset")
    reader = providers.StaticAssets(tmp_path, server.ASSET_NAMES)
    assert reader.asset("app.js") == b"// asset"


def test_the_asset_reader_answers_none_for_a_missing_directory(tmp_path: Path) -> None:
    reader = providers.StaticAssets(tmp_path / "absent", server.ASSET_NAMES)
    assert reader.asset("app.js") is None
