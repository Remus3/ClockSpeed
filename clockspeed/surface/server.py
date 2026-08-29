"""The local HTTPS listener: routing, static assets, and the log channel.

Owns (BOOTSTRAP.md section 7.2): the loopback TLS listener, the request-to-route
match, the frozen static asset set, the response headers every answer carries,
and - the part that is easiest to get wrong - every channel on which this
process is capable of writing a request to a stream.

THE SERVER DEPENDS ON THE ENDPOINTS AND NEVER THE REVERSE. ``contract.py`` states
the inversion and this module is the other half of it: a handler is
``Callable[[Mapping[str, str]], Response]``, so whatever provides a world or a
registry is bound into it by CLOSURE before the route is registered here. No
endpoint module imports this one, which is what lets an endpoint be tested
without standing up a listener.

ROUTING IS EXACT MATCHING AGAINST AUTHORED LITERALS. There is no path resolution
step anywhere below, for the static set or the API set, and that is a stronger
statement than "traversal is normalised away". ``GET /../../work/x.sav`` does not
fail a check - there is no check for it to fail, because the request path is only
ever compared for equality against three authored filenames and a table of route
templates, and it equals none of them. A template carrying a path parameter is
REFUSED at registration rather than supported: the handler signature admits query
parameters only, so a captured path segment would have nowhere to go, and a route
that silently never matches is worse than one that will not register.

WHY ``allow_reuse_address`` IS FALSE, MEASURED ON THIS MACHINE RATHER THAN
ASSUMED. Windows permits a second process to bind a port a first process is
actively LISTENING on when BOTH set ``SO_REUSEADDR``; with the flag on neither
side, or on only one, the second bind is refused (10048 when the challenger did
not set it, 10013 when it did but the incumbent had not). ``HTTPServer`` sets the
flag by DEFAULT, which is precisely the hijackable configuration - two dashboards
would both report success on one port and split traffic between them
nondeterministically. False breaks it from both directions at once: this process
never sets the flag as an incumbent, so a challenger that sets it is refused, and
never sets it as a challenger, so it is refused rather than silently succeeding.

THE PORT IS NEVER NEGOTIATED. A bind failure raises :class:`BindError`, whose
message names the port - a port number is not personal data - and points at the
allocation record and the environment check. Nothing retries, increments or falls
back. A dashboard listening somewhere other than where it was told to listen is
one the companion window cannot find, and answering "started" while doing that is
the plausible-rather-than-honest failure this project refuses at every other
layer, expressed at process level.

THE LOG CHANNEL IS A PERSONAL-DATA EGRESS PATH AND IS TREATED AS ONE. Four
stdlib paths write caller-chosen bytes by default and ALL FOUR are closed here:

  - ``log_request`` passes ``self.requestline`` - the RAW request line - into
    ``log_message``, which writes it to stderr.
  - ``log_error`` does the same on a malformed request, where those bytes are
    whatever arrived on the socket.
  - ``socketserver.BaseServer.handle_error`` prints a FULL TRACEBACK, whose
    frames carry local variables including the request.
  - ``send_error`` is the one the brief for this module did not name and the
    worst of the four, because it is not a log at all: it interpolates
    ``"Bad request version (%r)" % version`` and ``"Unsupported method (%r)" %
    self.command`` into the RESPONSE STATUS LINE AND BODY. Read from the 3.14
    source, not assumed.

So ``log_message`` and ``log_error`` are overridden to discard EVERY argument
rather than to sanitise them. That is deliberate: sanitising each stdlib call
site means auditing all of them and re-auditing on every upgrade, whereas a sink
that ignores its arguments is closed no matter which site fires or what a future
version passes. What this module logs instead, it composes itself from a matched
route TEMPLATE, a method checked against a closed set, and a status code - three
values that are authored in this repository or bounded by it. ``handle_error``
emits the exception TYPE NAME and nothing else, the idiom
``clockspeed/save/world.py`` states as ``WorldLoadError(stage, cause_type)``.

WHY A TRANSPORT FAULT RENDERS AS 404. ``send_error`` fires before any route
exists, and the published reason vocabulary has no spelling for "the request line
did not parse" - the nearest, ``malformed_query``, is about a query string and
would be a lie. Rather than invent a reason code, which is ``contract.py``'s
decision and not this module's, every such fault renders
``contract.no_such_route()``: nothing was parsed, so nothing matched, and the
envelope stays uniform and echoes nothing. The cost is stated plainly - a
malformed request line is answered 404 where 400 would be more precise.
"""

from __future__ import annotations

import ssl
import sys
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, Final, Protocol, runtime_checkable
from urllib.parse import parse_qsl

from clockspeed.surface.api import contract
from clockspeed.surface.config import LOOPBACK

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

    from clockspeed.surface.config import ServerConfig

__all__ = [
    "ASSET_NAMES",
    "EXIT_BIND_FAILED",
    "EXIT_CERTIFICATE",
    "EXIT_OK",
    "KNOWN_METHODS",
    "SERVER_BANNER",
    "STATIC_ROUTES",
    "AssetProvider",
    "BindError",
    "CertificateError",
    "RouteError",
    "bind_refusal",
    "build_server",
    "routing",
    "run",
    "serve",
    "shutdown_on_signal",
]


# ---------------------------------------------------------------------------
# The static set - a frozen three-name table, not a directory listing
# ---------------------------------------------------------------------------

#: Request path to (filename, content type). THE WHOLE STATIC SURFACE. Adding a
#: fourth entry is an edit to this literal and nothing else; there is no
#: directory walk, no suffix guess and no path join built from a request.
STATIC_ROUTES: Final[Mapping[str, tuple[str, str]]] = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}

#: The filenames the table names, which is the closed set the asset reader is
#: wired with. Derived from the table so the two cannot disagree.
ASSET_NAMES: Final = frozenset(name for name, _type in STATIC_ROUTES.values())

#: The only content type an API answer ever carries.
CONTENT_TYPE_JSON: Final = "application/json"

#: On the HTML response only. ``default-src 'none'`` denies everything not named
#: after it, so a future asset that reaches outward fails visibly here rather
#: than silently working - which is the point on a page rendering save-derived
#: content. ``connect-src 'self'`` is what lets the page call this same API.
CONTENT_SECURITY_POLICY: Final = (
    "default-src 'none'; script-src 'self'; style-src 'self'; "
    "connect-src 'self'; base-uri 'none'; form-action 'none'"
)

#: On EVERY response. ``no-store`` because a cached answer about a save is a
#: save-derived artifact sitting in a browser cache; ``nosniff`` because content
#: type guessing turns a JSON body into a script; ``no-referrer`` because the
#: dashboard URL carries the port and nothing downstream needs it.
FIXED_HEADERS: Final = (
    ("Cache-Control", "no-store"),
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "no-referrer"),
)


# ---------------------------------------------------------------------------
# Methods and identity
# ---------------------------------------------------------------------------

#: The closed method vocabulary. A method outside it is never logged and never
#: routed - ``self.command`` is caller-chosen text off the socket, so it is
#: matched against this set and rendered as :data:`UNKNOWN_METHOD` otherwise.
KNOWN_METHODS: Final = frozenset({"DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"})

#: What an unrecognised method is logged as. A literal, for the reason above.
UNKNOWN_METHOD: Final = "-"

#: What this server calls itself, in the Server header. The stdlib default is
#: ``BaseHTTP/<n> Python/3.14.4``, which discloses the exact interpreter patch
#: level to anything that connects, including the version of an unpatched
#: interpreter. This says nothing.
SERVER_BANNER: Final = "clockspeed"

#: The label a static answer is logged under. The matched FILENAME, which is
#: authored in this file, rather than the request path that matched it.
STATIC_LABEL_PREFIX: Final = "static:"


# ---------------------------------------------------------------------------
# Timing and lifetime
# ---------------------------------------------------------------------------

#: How often the serve loop checks whether it has been asked to stop.
POLL_INTERVAL: Final = 0.1

#: How long a shutdown or a thread join waits before giving up on it. A bound
#: rather than a budget: past it, ``server_close`` runs anyway, because the
#: listener being released is what the next start depends on.
SHUTDOWN_TIMEOUT: Final = 5.0

#: How long one connection may sit idle before its thread is released. Without
#: it, a client that opens a socket and never speaks holds a thread until the
#: process ends.
CONNECTION_TIMEOUT: Final = 30.0


# ---------------------------------------------------------------------------
# Exit codes and refusals. Every message below is a FIXED line.
# ---------------------------------------------------------------------------

EXIT_OK: Final = 0
EXIT_BIND_FAILED: Final = 2
EXIT_CERTIFICATE: Final = 3

ROUTE_NOT_A_TEMPLATE: Final = "a route template must be one this repository authored"
ROUTE_HAS_A_PATH_PARAMETER: Final = (
    "a route template may not carry a path parameter: a handler receives query "
    "parameters only, so a captured segment would have nowhere to go"
)
ROUTE_METHOD_UNKNOWN: Final = "a route method must be an uppercase member of the known set"
ROUTE_DUPLICATED: Final = "two routes claim the same method on the same template"
CERTIFICATE_UNUSABLE: Final = (
    "the dashboard certificate and key could not be loaded. Mint them with "
    "scripts/make_cert.py, or point CLOCKSPEED_CERT_DIR at the pair"
)


class RouteError(ValueError):
    """A route table could not be built. Carries a fixed line and echoes nothing."""


class CertificateError(Exception):
    """The TLS material could not be loaded.

    The message names the minting script and the override variable, and never
    the paths themselves - the override can point inside a home directory, and a
    home path is personal data under non-negotiable 3.
    """


def bind_refusal(port: int) -> str:
    """The one line an operator reads when the listener could not be bound.

    A MODULE-LEVEL FUNCTION RATHER THAN A METHOD, so the text has ONE author
    and neither the raise site nor :func:`run` renders an exception OBJECT to
    reach it. ``str()`` on a caught object is what its RUNTIME type decides:
    today both handlers in :func:`run` catch a type declared here carrying
    fixed text, and the day one ``except`` clause is widened to ``OSError`` the
    same spelling appends the path the call failed on, which carries the
    account name (non-negotiable 12). ``tests/test_exception_rendering.py``
    refuses the shape categorically for that reason, and this is the spelling
    that satisfies it: a named ``int`` field interpolated into text this module
    owns.

    Args:
        port: The port that could not be bound. A port number is not personal
            data, and naming it is the whole value of the message - an operator
            cannot act on "the dashboard did not start".

    Returns:
        The refusal, with no trailing newline. Byte-identical to what
        :class:`BindError` carries, which ``tests/surface/test_server.py``
        asserts on four ports so the two spellings cannot drift.
    """
    return (
        f"could not bind the dashboard on {LOOPBACK} port {port}. Nothing was "
        "started and NO OTHER PORT WAS TRIED, deliberately: a dashboard on an "
        "unexpected port is one the companion window cannot find. Check the "
        "allocation in config/ports.json and run scripts/verify_env.py."
    )


class BindError(Exception):
    """The listener could not be bound, and nothing was tried in its place.

    Attributes:
        port: The port that refused. A port number is not personal data, and
            naming it is the whole value of this message - an operator cannot
            act on "the dashboard did not start". It is also the NAMED FIELD
            :func:`run` renders, in place of the object itself.
    """

    def __init__(self, port: int) -> None:
        """Build the one-line message from the port and two fixed pointers.

        Args:
            port: The port that could not be bound.
        """
        self.port = port
        super().__init__(bind_refusal(port))


# ---------------------------------------------------------------------------
# What supplies the dashboard's own files
# ---------------------------------------------------------------------------


@runtime_checkable
class AssetProvider(Protocol):
    """Whatever hands the server one of its own static files.

    Named here rather than in ``contract.py`` because a static file is this
    module's business and no endpoint has one. ``None`` means "not servable",
    which is a 404 - including on a machine where the asset directory has not
    been created yet, because the asset slice may land after this one.
    """

    def asset(self, name: str) -> bytes | None:
        """The bytes of one named asset, or None.

        Args:
            name: A filename from :data:`ASSET_NAMES`.

        Returns:
            The bytes, or None.
        """
        ...


# ---------------------------------------------------------------------------
# The route table
# ---------------------------------------------------------------------------


def routing(routes: Sequence[contract.Route]) -> dict[str, dict[str, contract.Handler]]:
    """Build the template-to-method-to-handler table, refusing anything unroutable.

    Args:
        routes: The registered routes, each with its providers already bound in
            by closure.

    Returns:
        template -> method -> handler.

    Raises:
        RouteError: A template is not one this repository could have authored, or
            carries a path parameter, or a method is outside the known set, or
            two routes claim the same method on the same template. Each is a
            fixed line and none quotes the offending value: a route table is
            authored here, but a refusal that quotes its input is a formatting
            site waiting for the day one is not.
    """
    table: dict[str, dict[str, contract.Handler]] = {}
    for route in routes:
        if contract.ENDPOINT_PATTERN.fullmatch(route.template) is None:
            raise RouteError(ROUTE_NOT_A_TEMPLATE)
        if "<" in route.template:
            raise RouteError(ROUTE_HAS_A_PATH_PARAMETER)
        if route.method not in KNOWN_METHODS:
            raise RouteError(ROUTE_METHOD_UNKNOWN)
        bucket = table.setdefault(route.template, {})
        if route.method in bucket:
            raise RouteError(ROUTE_DUPLICATED)
        bucket[route.method] = route.handler
    return table


# ---------------------------------------------------------------------------
# The handler
# ---------------------------------------------------------------------------


class DashboardHandler(BaseHTTPRequestHandler):
    """Answers one request, and writes nothing anywhere that it did not compose.

    Every ``do_*`` below routes into one dispatcher, rather than leaving the
    unlisted ones to the stdlib: an undefined method reaches
    ``handle_one_request``, which calls ``send_error`` with the method
    interpolated into the reason phrase - a caller-chosen string on the status
    line. Defining them all means every method this server can be asked for is
    answered by code in this file.
    """

    #: HTTP/1.1 so the dashboard can keep a connection. Safe only because every
    #: response below sends an explicit Content-Length; a missing one on 1.1 is
    #: a hung client rather than a visible fault.
    protocol_version = "HTTP/1.1"

    #: Both halves of the default ``Server`` header, blanked at the source as
    #: well as through :meth:`version_string`, so a stdlib path that reads them
    #: directly discloses nothing either.
    server_version = SERVER_BANNER
    sys_version = ""

    #: Releases the thread behind an idle connection.
    timeout = CONNECTION_TIMEOUT

    def version_string(self) -> str:
        """Return a fixed token instead of the interpreter's version.

        Returns:
            :data:`SERVER_BANNER`.
        """
        return SERVER_BANNER

    # -- the four channels that leak by default ----------------------------

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Discard every stdlib log call, arguments included.

        THE ARGUMENTS ARE NOT SANITISED, THEY ARE DROPPED. ``log_request`` passes
        the raw request line through here; sanitising per call site means
        auditing every stdlib caller and re-auditing each upgrade, while a sink
        that ignores its inputs is closed whatever calls it. What this server
        does log, it composes in :meth:`_log`.

        Args:
            format: Ignored.
            args: Ignored.
        """

    def log_error(self, format: str, *args: object) -> None:  # noqa: A002
        """Discard every stdlib error log call, arguments included.

        Fires on a malformed request line, where the arguments are whatever
        arrived on the socket.

        Args:
            format: Ignored.
            args: Ignored.
        """

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:  # noqa: ARG002
        """Answer a pre-routing transport fault without echoing one byte of it.

        The stdlib builds ``"Bad request version (%r)"`` and ``"Unsupported
        method (%r)"`` from request bytes and puts the result on the STATUS LINE
        and in the BODY. Both arguments are ignored here and the published
        404 envelope is sent instead - see the module docstring for why 404
        rather than 400.

        Args:
            code: Ignored, deliberately.
            message: Ignored, deliberately.
            explain: Ignored, deliberately.
        """
        del code
        self._respond(contract.no_such_route(), contract.ENDPOINT_UNROUTED)

    # -- what this module logs instead -------------------------------------

    def _log(self, template: str, code: int) -> None:
        """Write the one log line this server emits.

        Three bounded values and nothing else: a method checked against
        :data:`KNOWN_METHODS`, a route TEMPLATE or a filename authored in this
        file, and an integer status.

        Args:
            template: The matched template, or a literal for what did not match.
            code: The HTTP status.
        """
        method = self.command if self.command in KNOWN_METHODS else UNKNOWN_METHOD
        sys.stderr.write(f"{method} {template} {code}\n")

    # -- responses ---------------------------------------------------------

    def _emit(self, code: int, body: bytes, content_type: str, *, csp: bool = False) -> None:
        """Write one complete response with the fixed header set.

        Args:
            code: The HTTP status.
            body: The already-encoded body.
            content_type: What the body is.
            csp: Whether to add the content security policy, which belongs on
                the HTML document alone.
        """
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in FIXED_HEADERS:
            self.send_header(name, value)
        if csp:
            self.send_header("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        self.end_headers()
        if self.command != "HEAD" and body:
            self.wfile.write(body)

    def _respond(self, response: contract.Response, template: str) -> None:
        """Encode and write one contract envelope.

        Args:
            response: What the route decided.
            template: What to log it under.
        """
        self._log(template, response.http_status)
        self._emit(response.http_status, contract.encode(response.payload), CONTENT_TYPE_JSON)

    # -- dispatch ----------------------------------------------------------

    def _query(self, raw: str) -> dict[str, str] | None:
        """Parse a query string into single-valued parameters.

        A REPEATED KEY IS MALFORMED RATHER THAN LAST-WINS. A handler receives a
        ``Mapping[str, str]``, so one of the two values would have to be
        discarded silently, and which one is discarded is exactly the ambiguity
        a parameter-smuggling request relies on.

        Args:
            raw: The query string, without the leading question mark.

        Returns:
            The parameters, or None when the query did not parse.
        """
        if not raw:
            return {}
        try:
            pairs = parse_qsl(raw, keep_blank_values=True, strict_parsing=True, errors="strict")
        except (ValueError, UnicodeDecodeError):
            return None
        params: dict[str, str] = {}
        for key, value in pairs:
            if key in params:
                return None
            params[key] = value
        return params

    def _serve_asset(self, filename: str, content_type: str) -> None:
        """Answer one static file, or 404 when it is not there.

        Args:
            filename: A name from :data:`ASSET_NAMES`, never a request path.
            content_type: What the table says it is.
        """
        provider: AssetProvider | None = self.server.assets  # type: ignore[attr-defined]
        body = None if provider is None else provider.asset(filename)
        if body is None:
            self._respond(contract.no_such_route(), contract.ENDPOINT_UNROUTED)
            return
        self._log(f"{STATIC_LABEL_PREFIX}{filename}", contract.HTTP_OK)
        self._emit(contract.HTTP_OK, body, content_type, csp=content_type.startswith("text/html"))

    def _dispatch(self) -> None:
        """Match the request against the two closed tables and answer it."""
        raw_path, _mark, raw_query = self.path.partition("?")

        static = STATIC_ROUTES.get(raw_path)
        if static is not None:
            if self.command in {"GET", "HEAD"}:
                self._serve_asset(*static)
                return
            # The contract cannot spell a static path - ENDPOINT_PATTERN admits
            # /api/... templates only - so the 405 names the unrouted literal.
            self._respond(
                contract.method_not_allowed(contract.ENDPOINT_UNROUTED),
                contract.ENDPOINT_UNROUTED,
            )
            return

        table: Mapping[str, Mapping[str, contract.Handler]] = self.server.routing_table  # type: ignore[attr-defined]
        bucket = table.get(raw_path)
        if bucket is None:
            self._respond(contract.no_such_route(), contract.ENDPOINT_UNROUTED)
            return

        handler = bucket.get(self.command)
        if handler is None and self.command == "HEAD":
            # RFC 9110: a resource answering GET must answer HEAD. The handler is
            # the same one and :meth:`_emit` suppresses the body, so the headers -
            # Content-Length included - describe the GET answer exactly. Without
            # this, every route would have to register HEAD by hand and the one
            # that forgot would 405 a method the specification requires.
            handler = bucket.get("GET")
        if handler is None:
            self._respond(contract.method_not_allowed(raw_path), raw_path)
            return

        params = self._query(raw_query)
        if params is None:
            self._respond(contract.bad_request(raw_path, contract.REASON_MALFORMED_QUERY), raw_path)
            return

        self._respond(handler(params), raw_path)

    def do_GET(self) -> None:
        """Answer a GET."""
        self._dispatch()

    def do_HEAD(self) -> None:
        """Answer a HEAD."""
        self._dispatch()

    def do_POST(self) -> None:
        """Answer a POST."""
        self._dispatch()

    def do_PUT(self) -> None:
        """Answer a PUT."""
        self._dispatch()

    def do_PATCH(self) -> None:
        """Answer a PATCH."""
        self._dispatch()

    def do_DELETE(self) -> None:
        """Answer a DELETE."""
        self._dispatch()

    def do_OPTIONS(self) -> None:
        """Answer an OPTIONS."""
        self._dispatch()


# ---------------------------------------------------------------------------
# The listener
# ---------------------------------------------------------------------------


class DashboardServer(ThreadingHTTPServer):
    """The loopback listener, with address reuse off and a silent error path."""

    #: So a stuck connection cannot keep the process alive after shutdown.
    daemon_threads = True

    #: MEASURED on this machine, not assumed - see the module docstring. The
    #: stdlib default is True, which is the hijackable setting.
    allow_reuse_address = False

    #: Same reasoning. A second listener on one port is never what was wanted.
    allow_reuse_port = False

    def __init__(
        self,
        address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
        table: Mapping[str, Mapping[str, contract.Handler]],
        assets: AssetProvider | None,
    ) -> None:
        """Wire the tables, then bind.

        Both attributes are set BEFORE the bind, because the bind can raise and
        a half-built server must not be reachable in that state.

        Args:
            address: (host, port). The host is asserted to be loopback by
                :func:`build_server` before this is reached.
            handler_class: The request handler.
            table: The route table from :func:`routing`.
            assets: What supplies the static files, or None for none.
        """
        self.routing_table = table
        self.assets = assets
        super().__init__(address, handler_class)

    def handle_error(self, request: object, client_address: object) -> None:
        """Report the exception TYPE and nothing else.

        The stdlib prints a full traceback here, whose frames carry local
        variables - the request among them. This emits the class name only, the
        idiom ``clockspeed/save/world.py`` states as
        ``WorldLoadError(stage, cause_type)``.

        Args:
            request: Ignored.
            client_address: Ignored.
        """
        del request, client_address
        raised = sys.exception()
        sys.stderr.write(f"request failed: {type(raised).__name__}\n")


# ---------------------------------------------------------------------------
# Construction and lifetime
# ---------------------------------------------------------------------------


def _tls_context(config: ServerConfig) -> ssl.SSLContext:
    """Build the server-side TLS context.

    ``ssl.wrap_socket`` - the module-level function - was REMOVED in Python
    3.14. A context plus :meth:`ssl.SSLContext.wrap_socket` is the only spelling
    that exists on this interpreter.

    Args:
        config: Where the pair lives.

    Returns:
        The context.

    Raises:
        CertificateError: The pair is absent, unreadable or does not match. The
            message names the minting script and never the paths.
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    try:
        context.load_cert_chain(config.cert_path, config.key_path)
    except (OSError, ssl.SSLError) as exc:
        raise CertificateError(CERTIFICATE_UNUSABLE) from exc
    return context


def build_server(
    config: ServerConfig,
    routes: Sequence[contract.Route],
    providers: AssetProvider | None = None,
) -> DashboardServer:
    """Bind the listener and wrap it in TLS, or refuse without falling back.

    The listening socket itself is wrapped, so every accepted connection is
    already through the handshake and no plaintext request is ever parsed.

    Args:
        config: The resolved configuration.
        routes: Routes with their providers already bound in by closure.
        providers: What supplies the static files, or None.

    Returns:
        The bound server, not yet serving.

    Raises:
        RouteError: The route table would not build.
        CertificateError: The TLS material would not load.
        BindError: The port could not be bound. NOTHING ELSE IS TRIED.
        ValueError: The configuration names an address other than loopback.
            Checked here rather than trusted, because the one thing this server
            must never do is listen where another machine can reach it.
    """
    if config.host != LOOPBACK:
        raise ValueError(f"the dashboard binds {LOOPBACK} and no other address")
    table = routing(routes)
    context = _tls_context(config)
    try:
        server = DashboardServer((config.host, config.port), DashboardHandler, table, providers)
    except OSError as exc:
        raise BindError(config.port) from exc
    server.socket = context.wrap_socket(server.socket, server_side=True)
    return server


@contextmanager
def serve(
    config: ServerConfig,
    routes: Sequence[contract.Route],
    providers: AssetProvider | None = None,
) -> Iterator[DashboardServer]:
    """Serve for the duration of the block, and release the listener on every exit.

    ``server_close`` RUNS ON EVERY PATH, including an exception raised inside the
    block and including a shutdown that does not complete. That is why the stop
    is issued from a helper thread and joined with a timeout rather than called
    directly: ``BaseServer.shutdown`` waits on an event the serve loop sets, so a
    serve loop that never started or already died would block it forever, and a
    blocked stop that prevented the close would leave the port held by a process
    that is no longer answering on it. Bounding the stop and closing regardless
    is what makes the next start possible.

    The stop is also never issued from the serving thread itself, which is the
    documented way to deadlock this class.

    Args:
        config: The resolved configuration.
        routes: Routes with their providers already bound in.
        providers: What supplies the static files, or None.

    Yields:
        The serving server. ``server.server_address[1]`` is the real port, which
        is how a caller that asked for port 0 learns what it got.
    """
    server = build_server(config, routes, providers)
    thread = threading.Thread(
        target=server.serve_forever,
        kwargs={"poll_interval": POLL_INTERVAL},
        daemon=True,
        name="clockspeed-serve",
    )
    thread.start()
    try:
        yield server
    finally:
        stopper = threading.Thread(target=server.shutdown, daemon=True, name="clockspeed-stop")
        stopper.start()
        stopper.join(SHUTDOWN_TIMEOUT)
        server.server_close()
        thread.join(SHUTDOWN_TIMEOUT)


def shutdown_on_signal(server: DashboardServer) -> object:
    """Build a SIGINT handler that stops the server from a SEPARATE thread.

    ``BaseServer.shutdown`` blocks until the serve loop acknowledges. A signal
    handler runs on the main thread, and if the main thread is the one inside
    ``serve_forever`` the call waits for a loop that cannot proceed until the
    handler returns - the documented deadlock. Handing the stop to a fresh
    thread means the handler returns at once whatever the main thread was doing.

    Args:
        server: The server to stop.

    Returns:
        The handler, for :func:`signal.signal`.
    """

    def _handler(signum: int, frame: object) -> None:
        del signum, frame
        threading.Thread(target=server.shutdown, daemon=True, name="clockspeed-sigint").start()

    return _handler


def run(
    config: ServerConfig,
    routes: Sequence[contract.Route],
    providers: AssetProvider | None = None,
    *,
    stop: threading.Event | None = None,
) -> int:
    """Serve until stopped, and turn every refusal into a distinct exit code.

    THE ROUTE LIST IS AN ARGUMENT AND IS NOT ASSEMBLED HERE. Endpoint modules are
    the wiring slice's to import; this module deliberately imports none of them,
    which is the same inversion ``contract.py`` records - the server depends on
    the endpoints, so the endpoints stay testable without a listener.

    Args:
        config: The resolved configuration.
        routes: Routes with their providers already bound in.
        providers: What supplies the static files, or None.
        stop: Set to end the run. None waits until the process is signalled.

    Returns:
        :data:`EXIT_OK`, or a distinct non-zero code per refusal so a runbook can
        branch on it. A bind failure NEVER retries another port.
    """
    gate = threading.Event() if stop is None else stop
    try:
        with serve(config, routes, providers) as server:
            signal_handler = shutdown_on_signal(server)
            _install_sigint(signal_handler)
            gate.wait()
    except CertificateError:
        # NEITHER HANDLER RENDERS THE OBJECT IT CAUGHT, and that is a rule about
        # the RUNTIME TYPE rather than about today's message. Both types are
        # declared in this module and carry fixed text, so `f"{exc}"` leaks
        # nothing as the code stands - but widening either `except` to `OSError`
        # turns the same spelling into a home-path leak, because `str()` on an
        # OSError appends the path it failed on. The constant below is the only
        # argument any raise site passes to `CertificateError`, asserted by
        # `test_every_certificate_refusal_is_raised_with_the_one_constant`.
        sys.stderr.write(f"{CERTIFICATE_UNUSABLE}\n")
        return EXIT_CERTIFICATE
    except BindError as exc:
        sys.stderr.write(f"{bind_refusal(exc.port)}\n")
        return EXIT_BIND_FAILED
    return EXIT_OK


def _install_sigint(handler: object) -> None:
    """Install a SIGINT handler when the platform and thread allow it.

    ``signal.signal`` raises off the main thread and on a platform without the
    signal. Neither is a reason to refuse to serve, so both are tolerated: the
    server is still stoppable through its own event.

    Args:
        handler: What :func:`shutdown_on_signal` built.
    """
    import signal  # noqa: PLC0415

    try:
        signal.signal(signal.SIGINT, handler)  # type: ignore[arg-type]
    except (ValueError, OSError, AttributeError):
        return
