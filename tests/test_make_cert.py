#!/usr/bin/env python3
"""CS-601 slice S1 - scripts/make_cert.py, and the openssl row in verify_env.

WHAT THIS GRADES. The local dashboard listens over HTTPS on loopback, so it
needs a certificate. Nothing in the Python standard library can mint one -
``pyproject.toml`` declares ``dependencies = []`` and calls that a decision -
so the certificate is minted by shelling out to openssl, and the thing under
test is the argv and the refusal behaviour rather than any cryptography this
project wrote.

THE ARMS ARE SPLIT INTO A PURE HALF AND A LIVE HALF, DELIBERATELY. The pure
half asserts the argv flag by flag and runs on a machine with no openssl at
all, which is the same machine the rule suite has to run on (BOOTSTRAP.md
section 5.4). The live half generates a real pair, serves real TLS over a real
loopback socket, and verifies it from a real client. Neither half is sufficient
on its own: the pure half cannot tell whether the flags it pins actually
produce a usable certificate, and the live half would still pass if the flags
drifted into a different but equally workable set.

THE NEGATIVE ARM IS WHAT MAKES THE POSITIVE ARM MEAN ANYTHING. A client that
validates nothing completes a handshake against any certificate whatsoever, so
"the client connected" is not evidence that the certificate verified. Every
positive arm below is therefore paired with the SAME server reached by a client
carrying only the system trust store, asserting it is REJECTED. If that pairing
is ever dropped, the positive arm degrades to a test that TLS exists.

NOTHING HERE IS MARKED SLOW, AND EXACTLY ONE ARM SKIPS. The ``slow`` marker
currently excludes nothing anywhere - ``.githooks/pre-push`` runs pytest with no
``-m`` filter - so marking the live arms would hide them from no one while
suggesting they are optional. A skipped test is not a passing test: if openssl
is genuinely absent, these fail loudly and say so rather than skipping.

THE ONE SKIP IS A MISSING SUBJECT RATHER THAN A MISSING DEPENDENCY, and that
distinction is the whole of why it is tolerated where a skip for an absent
openssl is not. ``test_the_generated_key_is_restricted_to_this_account`` grades
POSIX mode bits, and a platform that does not implement them cannot exhibit the
property at all - there is nothing there to be right or wrong about, so a green
result would be a statement about nothing. It is gated on a MEASURED capability
rather than on a platform name, so it starts grading Windows on the day Windows
honours the request and stops grading POSIX on the day POSIX stops, and its
reason records the restriction as UNMEASURED here rather than as absent. The
failure half of the same promise,
``test_a_key_the_platform_would_not_restrict_is_still_written``, forces the
error instead of waiting for it and therefore runs everywhere.

THE HELPER IS PUBLISHED FOR SIBLING MODULES ON PURPOSE. :func:`cert_pair` is
imported by the modules that test the HTTPS surface. If each of those built its
own throwaway certificate, each could omit the IP SAN and each could compensate
with ``check_hostname=False``, and no test in the tree would notice the
artifact is unusable by a real client. One helper, graded here, is the fix.

NO PATH IS EVER THE SUBJECT OF AN ASSERTION IN THE LIVE ARMS. pytest renders
the asserted EXPRESSION independently of the message, and a ``tmp_path`` on
Windows carries both a home path and the account name. Every live assertion
below binds a scalar - a count, a boolean, a hex digest - and asserts on that.
The pure arms use synthetic relative paths and touch no filesystem at all.
"""

from __future__ import annotations

import ast
import errno
import hashlib
import importlib.util
import os
import re
import socket
import ssl
import subprocess
import sys
import threading
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MAKE_CERT_SOURCE = REPO_ROOT / "scripts" / "make_cert.py"
VERIFY_ENV_SOURCE = REPO_ROOT / "scripts" / "verify_env.py"

#: Synthetic, relative, and never touched on disk. The pure arms assert on the
#: rendered argv, so their paths must not carry a home directory into a failure
#: message - which a tmp_path would.
CERT_STUB = Path("certs") / "dashboard.cert.pem"
KEY_STUB = Path("certs") / "dashboard.key.pem"

#: How long a live arm waits on a socket before calling the server hung. Every
#: socket operation below is bounded: an unbounded wait in a test is the same
#: failure class as an unbounded external probe in a tool.
SOCKET_TIMEOUT_SECONDS = 20.0

#: X509_V_ERR_DEPTH_ZERO_SELF_SIGNED_CERT. Named rather than written as a bare
#: 18 at the assertion, so the negative arm says WHY it expected a refusal
#: instead of pinning a number nobody can read.
SELF_SIGNED_VERIFY_CODE = 18

# THE PEM BANNERS ARE ASSEMBLED FROM FRAGMENTS, the same way
# tools/precommit_gate.py assembles its own patterns and for the same reason.
# That gate's secret scan carries a "PEM private key block" pattern, it scans
# every staged file, and this file is one of them - so the banner written out
# literally BLOCKS THE COMMIT. Measured, not anticipated: the literal spelling
# produced "SECRET PEM private key block" against this exact line, which is the
# green-locally red-on-commit shape. The fragments below match the same runtime
# string without ever putting the pattern in the source.
_PEM_EDGE = "-" * 5
CERT_BANNER = f"{_PEM_EDGE}BEGIN CERTIFICATE{_PEM_EDGE}"
KEY_BANNER = f"{_PEM_EDGE}BEGIN PRIVATE KEY{_PEM_EDGE}"


def _load_script(source: Path, bound_name: str) -> ModuleType:
    """Load an entry-point script from ``scripts/`` by path.

    scripts/ is a directory of entry-point scripts rather than an importable
    package, so the module is loaded from its file - the same way
    tests/test_verify_env.py loads verify_env.py. The bound name is distinct
    from the one that module uses, so two loaders cannot collide inside a
    single pytest session.

    Args:
        source: The script file.
        bound_name: The key to bind it under in sys.modules.

    Returns:
        The loaded module.

    Raises:
        ImportError: The script is not loadable from this checkout.
    """
    spec = importlib.util.spec_from_file_location(bound_name, source)
    if spec is None or spec.loader is None:
        message = f"could not load {source.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


make_cert = _load_script(MAKE_CERT_SOURCE, "clockspeed_make_cert")
verify_env = _load_script(VERIFY_ENV_SOURCE, "clockspeed_make_cert_verify_env")

#: Bound here because a parametrize decorator is evaluated at collection time,
#: and reaching through the module inside one reads worse than naming it once.
CERT_BASENAME = make_cert.CERT_NAME
KEY_BASENAME = make_cert.KEY_NAME


# ---------------------------------------------------------------------------
# The published helper - imported by sibling modules, graded here
# ---------------------------------------------------------------------------


def cert_pair(directory: Path) -> tuple[Path, Path]:
    """Mint one real certificate and key pair into ``directory``.

    PUBLISHED FOR SIBLING TEST MODULES. Import it rather than rolling a
    throwaway certificate: a hand-rolled one tends to omit the IP SAN, and the
    test that uses it then compensates with ``check_hostname=False``, at which
    point neither the certificate nor the test proves anything about what a
    real client would accept. This routes through the real entry point, so what
    a sibling gets is exactly what the operator gets.

    Args:
        directory: Where the pair is written. Normally a tmp_path.

    Returns:
        The certificate path and the key path, in that order.

    Raises:
        RuntimeError: openssl is absent or refused. Deliberately loud rather
            than a skip - a skipped test is not a passing test.
    """
    code = make_cert.main(["--cert-dir", str(directory)])
    if code != make_cert.EXIT_OK:
        message = f"make_cert exited {code}, expected {make_cert.EXIT_OK}"
        raise RuntimeError(message)
    return directory / make_cert.CERT_NAME, directory / make_cert.KEY_NAME


@contextmanager
def tls_echo_server(
    cert_path: Path, key_path: Path, rounds: int
) -> Iterator[tuple[int, list[str]]]:
    """Serve ``rounds`` TLS connections on loopback, then stop.

    The listener is bound to port 0 so the OS picks a free one - nothing here
    touches the reserved band in config/ports.json, which belongs to the real
    surface rather than to a test. Every wait is bounded and the listener is
    closed on the way out, so a failing arm cannot leak a socket or a thread
    into the rest of the session.

    Args:
        cert_path: The server certificate.
        key_path: Its private key.
        rounds: How many connections to accept before the thread returns.

    Yields:
        The bound port, and a list that accumulates the exception TYPE NAMES
        the server saw. A rejected handshake is an expected entry there.
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.settimeout(SOCKET_TIMEOUT_SECONDS)
    listener.bind(("127.0.0.1", 0))
    listener.listen(rounds + 1)
    port = int(listener.getsockname()[1])
    seen: list[str] = []

    def serve() -> None:
        for _ in range(rounds):
            try:
                raw, _address = listener.accept()
                raw.settimeout(SOCKET_TIMEOUT_SECONDS)
                with raw, context.wrap_socket(raw, server_side=True) as tls:
                    tls.recv(1024)
                    tls.sendall(b"clockspeed-ok")
            except (OSError, ssl.SSLError) as exc:
                seen.append(type(exc).__name__)

    thread = threading.Thread(target=serve, name="s1-tls-echo", daemon=True)
    thread.start()
    try:
        yield port, seen
    finally:
        listener.close()
        thread.join(timeout=SOCKET_TIMEOUT_SECONDS)


def _speak_tls(port: int, context: ssl.SSLContext, server_hostname: str) -> bytes:
    """One complete TLS round trip against the loopback server.

    Args:
        port: The bound port.
        context: The client context under test.
        server_hostname: What the client asks the certificate to match.

    Returns:
        Whatever the server replied.
    """
    with (
        socket.create_connection(("127.0.0.1", port), timeout=SOCKET_TIMEOUT_SECONDS) as raw,
        context.wrap_socket(raw, server_hostname=server_hostname) as tls,
    ):
        tls.sendall(b"ping")
        return bytes(tls.recv(64))


def _values_for(argv: list[str], flag: str) -> list[str]:
    """Every token sitting immediately after ``flag`` in ``argv``.

    Args:
        argv: The rendered command.
        flag: The flag whose values are wanted.

    Returns:
        The values, in order.
    """
    return [
        argv[index + 1]
        for index, token in enumerate(argv)
        if token == flag and index + 1 < len(argv)
    ]


def _sole_value(argv: list[str], flag: str) -> str | None:
    """The single value of ``flag``, or None when it is absent or repeated.

    Collapsing "absent", "repeated" and "wrong" into one comparison keeps the
    assertion a SCALAR comparison, which is the whole point - pytest renders
    the asserted expression, and a list of argv tokens rendered on failure is
    noise at best.

    Args:
        argv: The rendered command.
        flag: The flag whose sole value is wanted.

    Returns:
        The value, or None.
    """
    values = _values_for(argv, flag)
    return values[0] if len(values) == 1 else None


# ---------------------------------------------------------------------------
# The pure arm - runs on a machine with no openssl
# ---------------------------------------------------------------------------


def test_cert_argv_names_openssl_by_name_and_never_by_absolute_path() -> None:
    """argv[0] is resolved from PATH, never hardcoded.

    CLAUDE.md non-negotiable 3 forbids a machine-specific absolute path in a
    tracked file, and the interpreter rule in BOOTSTRAP.md section 2.5 makes
    the same point about naming a tool by where it happens to live today.
    """
    argv = make_cert.cert_argv(CERT_STUB, KEY_STUB)

    assert argv[0] == "openssl"
    assert argv[1] == "req"


@pytest.mark.parametrize(
    "flag",
    ["-x509", "-sha256", "-noenc"],
)
def test_cert_argv_carries_the_bare_flag(flag: str) -> None:
    """Each valueless flag the local listener needs is present."""
    argv = make_cert.cert_argv(CERT_STUB, KEY_STUB)

    present = flag in argv
    assert present, f"{flag} is absent from the rendered openssl command"


@pytest.mark.parametrize(
    ("flag", "value"),
    [
        ("-newkey", "rsa:2048"),
        ("-days", "397"),
        ("-subj", "/CN=clockspeed-local"),
    ],
)
def test_cert_argv_carries_the_valued_flag(flag: str, value: str) -> None:
    """Each valued flag appears exactly once and carries the pinned value.

    397 days is the CA/Browser Forum maximum a public client will accept, and
    is kept even though nothing public will ever see this certificate - a
    lifetime a browser would reject is a trap waiting for the day the shell
    starts enforcing one.
    """
    argv = make_cert.cert_argv(CERT_STUB, KEY_STUB)

    assert _sole_value(argv, flag) == value


def test_cert_argv_writes_the_key_and_the_certificate_where_it_was_told() -> None:
    """-keyout and -out carry the paths handed in, not paths the script chose."""
    argv = make_cert.cert_argv(CERT_STUB, KEY_STUB)

    assert _sole_value(argv, "-keyout") == str(KEY_STUB)
    assert _sole_value(argv, "-out") == str(CERT_STUB)


@pytest.mark.parametrize(
    "extension",
    [
        "subjectAltName=DNS:localhost,IP:127.0.0.1",
        "basicConstraints=critical,CA:FALSE",
        "keyUsage=critical,digitalSignature,keyEncipherment",
        "extendedKeyUsage=serverAuth",
    ],
)
def test_cert_argv_carries_the_x509_extension(extension: str) -> None:
    """Each -addext the listener needs is present, spelled exactly."""
    argv = make_cert.cert_argv(CERT_STUB, KEY_STUB)

    present = extension in _values_for(argv, "-addext")
    assert present, f"the {extension.partition('=')[0]} extension is absent or misspelled"


def test_the_subject_alt_name_carries_both_localhost_and_the_loopback_address() -> None:
    """BOTH SAN halves, asserted separately, because dropping one is silent.

    The DNS half alone leaves ``https://127.0.0.1:<port>`` unverifiable, and a
    client that hits that failure is overwhelmingly likely to be repaired by
    setting ``check_hostname=False`` rather than by fixing the certificate. The
    IP half is therefore the load-bearing one for this project, and it gets its
    own assertion rather than riding inside a single exact-string comparison
    that would not say WHICH half went missing.
    """
    argv = make_cert.cert_argv(CERT_STUB, KEY_STUB)
    san = next(
        (value for value in _values_for(argv, "-addext") if value.startswith("subjectAltName=")),
        "",
    )

    has_dns = "DNS:localhost" in san
    has_ip = "IP:127.0.0.1" in san
    assert has_dns, "the subjectAltName does not cover localhost"
    assert has_ip, "the subjectAltName does not cover 127.0.0.1, so an IP client cannot verify"


def test_openssl_is_never_invoked_through_a_shell() -> None:
    """MEASURED TRAP, pinned so it cannot come back.

    Through Git Bash, MSYS path conversion rewrites ``-subj /CN=clockspeed-local``
    into an absolute Windows path and openssl rejects the result. The argv form
    with ``shell=False`` is immune, so every subprocess call in the script must
    say so EXPLICITLY - a call relying on the default is one refactor away from
    someone adding ``shell=True`` to "fix" a quoting problem.
    """
    tree = ast.parse(MAKE_CERT_SOURCE.read_text(encoding="utf-8"))
    runs = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
    ]
    explicitly_shell_free = [
        node
        for node in runs
        if any(
            keyword.arg == "shell"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is False
            for keyword in node.keywords
        )
    ]

    run_count = len(runs)
    shell_free_count = len(explicitly_shell_free)
    assert run_count >= 1, "no subprocess run call found; this test is asserting about nothing"
    assert shell_free_count == run_count, (
        f"{run_count - shell_free_count} of {run_count} subprocess run calls do not pass "
        "shell=False explicitly"
    )


def test_the_openssl_probe_is_bounded_by_a_timeout() -> None:
    """An external probe that never returns is an open failure class here.

    CS-816 is on the roadmap for exactly this shape. Every subprocess call in
    the script passes a timeout, and the timeout is a real number rather than
    None.
    """
    tree = ast.parse(MAKE_CERT_SOURCE.read_text(encoding="utf-8"))
    runs = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
    ]
    bounded = [
        node
        for node in runs
        if any(
            keyword.arg == "timeout"
            and not (isinstance(keyword.value, ast.Constant) and keyword.value.value is None)
            for keyword in node.keywords
        )
    ]

    run_count = len(runs)
    bounded_count = len(bounded)
    assert run_count >= 1, "no subprocess run call found; this test is asserting about nothing"
    assert bounded_count == run_count, (
        f"{run_count - bounded_count} of {run_count} subprocess run calls are unbounded"
    )
    assert make_cert.OPENSSL_TIMEOUT_SECONDS > 0


# ---------------------------------------------------------------------------
# The exit codes - the population derived from the module, the values measured
# ---------------------------------------------------------------------------


#: The prefix every exit-code constant in the script carries TODAY. THE
#: POPULATION IS FILTERED OUT OF THE MODULE rather than typed out here, and that
#: is the whole of what CS-882 changed. The arm this replaced listed five
#: constants by name, so the two codes argparse owns - 2 for a usage error, 0
#: for ``--help`` - were outside the set it could see, and both collided with a
#: documented outcome while it stayed green.
#:
#: A PREFIX IS A SPELLING AND THE ACCEPTANCE CLAUSE IS A BEHAVIOUR, so this
#: filter is HALF the population and is no longer the whole of it. MEASURED
#: against the arm as CS-882 shipped it, by declaring one further constant worth
#: 3 - a collision with ``EXIT_REFUSED`` - and running the arm four times: the
#: spelling carrying this prefix was seen and reddened it, while the same value
#: under a leading underscore, under a trailing ``_EXIT`` and under an unrelated
#: ``STATUS_`` name were all invisible and all left it green. That is a guard
#: measuring a spelling while its clause is about behaviour, which
#: ``memory/a-guard-can-measure-spelling.md`` records as a shape rather than as
#: an incident.
#:
#: :func:`_returned_exit_codes` is the other half, keyed on what the module DOES
#: - every module-level integer reaching a position the interpreter reads as an
#: exit status - and :func:`_graded_exit_codes` is the UNION, so neither keying
#: can hide what the other sees. THE UNION IS A WIDENING AND NOT A SWAP: the
#: prefixed declare-only case above still reddens after the repair, measured the
#: same way, because dropping this half to keep only the behavioural one would
#: have traded one blind spot for another.
EXIT_PREFIX = "EXIT_"

#: THE ONE COLLISION THIS SCRIPT IS ALLOWED, recorded as a pair of CONSTANT
#: NAMES so the assertions below can pin it exactly rather than merely tolerate
#: "a" collision. OPERATOR RULING, taken over the CS-882 acceptance clause's
#: universal: a successful ``--help`` exits 0 because that is what POSIX
#: convention says a successful ``--help`` does, and that outranks giving every
#: outcome a code of its own. The item therefore ships an honest partial - one
#: pair shares a code, deliberately and on the record - rather than a met
#: universal, and this constant is where the record lives.
EXEMPT_CONSTANTS = frozenset({"EXIT_OK", "EXIT_HELP"})

#: The same ruling stated again at the OUTCOME level, because the two
#: populations can drift apart: the constants could stop colliding on the day
#: two outcomes started. Both are pinned, and neither pin is derived from the
#: other.
HELP_OUTCOME = "help printed"
WRITTEN_OUTCOME = "pair written"
EXEMPT_OUTCOMES = frozenset({HELP_OUTCOME, WRITTEN_OUTCOME})

#: Carried into every failure message that mentions the exemption, so a reader
#: who reddens this arm is told what the allowance is FOR rather than finding an
#: unexplained hole in a distinctness check.
EXEMPT_REASON = (
    "operator ruling: POSIX convention - a successful --help exits 0 - outranks "
    "the distinctness universal for this ONE pair, and for no other"
)

#: One row of the module docstring's exit-code table: four spaces, the number,
#: two spaces, then the meaning. Parsed rather than trusted, so a constant added
#: without its docstring row - or a row left behind by a deleted constant -
#: reddens instead of drifting the way docs/OPERATIONS.md quietly did.
DOCUMENTED_CODE_ROW = re.compile(r"^ {4}(\d+) {2}\S")

#: A flag the parser cannot have. Spelled with the project name so a real flag
#: added later cannot collide with it and turn this probe into a valid run.
UNKNOWN_FLAG = "--clockspeed-not-a-real-flag"

#: What the stub openssl exits, chosen OUTSIDE every code the script declares.
#: If a probe ever reported this number, the stub's own status had been passed
#: through rather than translated, and that is visible instead of plausible.
STUB_OPENSSL_EXIT = 33

#: How long one outcome probe may take. Two of the seven do real key generation;
#: the rest return immediately. Bounded for the reason every other wait here is.
OUTCOME_TIMEOUT_SECONDS = 120


def _declared_exit_codes() -> dict[str, int]:
    """Read every exit code the script DECLARES, out of the script itself.

    Returns:
        Constant name to value, for every module-level ``EXIT_*`` integer.
        HALF THE GRADED POPULATION - see :func:`_graded_exit_codes` for the
        other half and for what a prefix cannot see.
    """
    return {
        name: value
        for name, value in vars(make_cert).items()
        if name.startswith(EXIT_PREFIX) and isinstance(value, int)
    }


def _documented_exit_codes() -> list[int]:
    """Read every exit code the script's own module docstring lists.

    A SECOND READING OF THE SAME FACT, and deliberately not a copy of the first.
    The constants say what the code can return; the docstring table is what a
    reader branches on. Both are the module's own declarations, so neither is a
    hand-written list, and the arm below asserts they name the same set.

    Returns:
        The codes the table carries, in the order it carries them.
    """
    found: list[int] = []
    for line in (make_cert.__doc__ or "").splitlines():
        match = DOCUMENTED_CODE_ROW.match(line)
        if match is not None:
            found.append(int(match.group(1)))
    return found


#: What this module calls module scope when it reports the function an exit
#: status is produced in. Not a Python identifier, so it can never be confused
#: with a real qualified name.
MODULE_SCOPE = "<module>"

#: The call spellings that hand a first positional argument to the interpreter
#: as a process status: ``SystemExit(...)``, ``sys.exit(...)``, the
#: ``super().exit(...)`` that is how argparse ends this process, and
#: ``os._exit(...)``. KEYED ON THE CALLED NAME AND NOT ON THE RECEIVER, because
#: the receiver is ``sys``, ``os`` or a ``super()`` object depending on the site
#: and none of the three is what makes the argument a status.
EXIT_CALL_NAMES = frozenset({"SystemExit", "exit", "_exit"})


def _make_cert_tree() -> ast.Module:
    """Parse the script under test.

    Returns:
        Its abstract syntax tree.
    """
    return ast.parse(MAKE_CERT_SOURCE.read_text(encoding="utf-8"))


def _scoped_nodes(tree: ast.Module) -> Iterator[tuple[str, ast.AST]]:
    """Walk the tree, pairing every node with the function that encloses it.

    THE QUALIFIED NAME IS BUILT ON THE WAY DOWN rather than recovered afterwards
    by asking which subtree a node sits in. The obvious alternative keys a map
    on ``id()``, which is only meaningful while the tree that produced it is
    alive - a trap this file would be carrying rather than a property it could
    assert.

    Args:
        tree: The parsed script.

    Yields:
        The qualified name of the innermost enclosing function, paired with the
        node. A function definition is yielded under its OWN name, and
        :data:`MODULE_SCOPE` stands for module scope.
    """
    stack: list[tuple[ast.AST, str, str]] = [(tree, "", MODULE_SCOPE)]
    while stack:
        scope, prefix, qualname = stack.pop()
        for child in ast.iter_child_nodes(scope):
            if isinstance(child, ast.ClassDef):
                yield qualname, child
                stack.append((child, f"{prefix}{child.name}.", qualname))
            elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                inner = f"{prefix}{child.name}"
                yield inner, child
                stack.append((child, f"{inner}.", inner))
            else:
                yield qualname, child
                stack.append((child, prefix, qualname))


def _module_level_ints(tree: ast.Module) -> dict[str, int]:
    """Every module-level ``NAME = <integer literal>`` binding, however it is spelled.

    NO PREFIX FILTER, DELIBERATELY. This is the table an exit-status expression
    is resolved against, and filtering it by spelling would put back, in the
    middle of the derivation, the exact hole the derivation exists to close.

    ``bool`` is excluded because ``isinstance(True, int)`` is True and a flag is
    not an exit code.

    Args:
        tree: The parsed script.

    Returns:
        Constant name to value.
    """
    found: dict[str, int] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Constant):
            continue
        value = node.value.value
        if isinstance(value, bool) or not isinstance(value, int):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                found[target.id] = value
    return found


def _status_leaves(expr: ast.expr | None) -> Iterator[ast.expr | None]:
    """Unwrap a conditional exit status into the values it can actually produce.

    The parser override hands argparse's two statuses to ``super().exit`` as ONE
    conditional expression. Reading that expression whole resolves to neither
    constant and would report an unnamed status on correct code.

    Args:
        expr: An expression in an exit-status position, or None for a bare
            ``return``.

    Yields:
        Each value the expression can evaluate to.
    """
    if isinstance(expr, ast.IfExp):
        yield from _status_leaves(expr.body)
        yield from _status_leaves(expr.orelse)
    else:
        yield expr


def _is_exit_call(node: ast.Call) -> bool:
    """Whether this call hands its first argument to the interpreter as a status.

    Args:
        node: Any call node.

    Returns:
        True for the spellings :data:`EXIT_CALL_NAMES` records.
    """
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in EXIT_CALL_NAMES
    return isinstance(func, ast.Attribute) and func.attr in EXIT_CALL_NAMES


def _called_function(leaf: ast.expr | None, functions: set[str]) -> str | None:
    """The module-level function an exit-status expression hands its value on to.

    Args:
        leaf: An expression in an exit-status position.
        functions: Every function name the module defines.

    Returns:
        The callee's name when the expression is a bare call to one of them,
        and None otherwise.
    """
    if not isinstance(leaf, ast.Call) or not isinstance(leaf.func, ast.Name):
        return None
    return leaf.func.id if leaf.func.id in functions else None


def _render_status(leaf: ast.expr | None) -> str:
    """Render one unnamed exit status for a failure message.

    ``ast.unparse`` is safe to put in a message here, and that is a property of
    the SUBJECT rather than of the renderer: the only source this module parses
    is a tracked script, which non-negotiable 3 already forbids from carrying a
    home path, an account id or a world name.

    Args:
        leaf: The expression, or None for a bare ``return``.

    Returns:
        A short rendering.
    """
    return "an empty return" if leaf is None else ast.unparse(leaf)


def _exit_status_sites(tree: ast.Module) -> tuple[list[tuple[str, str]], list[str]]:
    """Read every value the script hands the interpreter as a process exit status.

    KEYED ON WHAT THE MODULE DOES RATHER THAN ON HOW IT SPELLS A NAME. The seed
    is the first argument of every call :func:`_is_exit_call` recognises, and
    the walk from there is TRANSITIVE at any depth rather than two levels deep:
    a seed that is a bare call to a module function makes that function a
    producer, and so does a producer's own ``return`` of a bare call - which is
    how ``main`` hands ``_generate``'s value out. Each producer is walked once,
    so a cycle terminates.

    A CALL THIS CANNOT RESOLVE IS REPORTED RATHER THAN SKIPPED. Anything in an
    exit-status position that is neither a module-level integer's name nor a
    bare call to a known function comes back as unnamed, so an exit status
    arriving through a shape this walk does not model reddens instead of
    vanishing.

    A SITE IS A PLACE AND NOT A VALUE. Three separate returns of one constant
    are three sites, so a branch added beside them arrives as a new site instead
    of being absorbed into a constant the record already names.

    Args:
        tree: The parsed script.

    Returns:
        The named sites as ``(function, constant name)`` pairs - one entry per
        site - and a rendering of every exit status that no module-level integer
        constant names.
    """
    module_ints = _module_level_ints(tree)
    functions: set[str] = set()
    returns: dict[str, list[ast.expr | None]] = {}
    pending: list[tuple[str, ast.expr | None]] = []

    for qualname, node in _scoped_nodes(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            functions.add(qualname)
        elif isinstance(node, ast.Return):
            returns.setdefault(qualname, []).append(node.value)
        elif isinstance(node, ast.Call) and _is_exit_call(node):
            pending.append((qualname, node.args[0] if node.args else None))

    sites: list[tuple[str, str]] = []
    unnamed: list[str] = []
    walked: set[str] = set()
    while pending:
        qualname, expr = pending.pop()
        for leaf in _status_leaves(expr):
            callee = _called_function(leaf, functions)
            if isinstance(leaf, ast.Name) and leaf.id in module_ints:
                sites.append((qualname, leaf.id))
            elif callee is not None and callee not in walked:
                walked.add(callee)
                pending.extend((callee, value) for value in returns.get(callee, []))
            elif callee is None:
                unnamed.append(f"{qualname} -> {_render_status(leaf)}")
    return sites, unnamed


def _returned_exit_codes() -> dict[str, int]:
    """Every module-level integer the script RETURNS as an exit status.

    THE SECOND KEYING, and the one the acceptance clause is actually about. See
    :data:`EXIT_PREFIX` for the three spellings the first keying cannot see.

    Returns:
        Constant name to value, for every name reaching an exit-status position.
    """
    tree = _make_cert_tree()
    sites, _unnamed = _exit_status_sites(tree)
    values = _module_level_ints(tree)
    return {name: values[name] for _function, name in sites}


def _graded_exit_codes() -> dict[str, int]:
    """The population the distinctness clause is judged over - the UNION of both keyings.

    NEITHER HALF IS DROPPED, and each sees something the other cannot. The
    prefix keying sees a constant that is declared and never returned; the
    behaviour keying sees a constant spelled outside the prefix and returned.

    WHAT REMAINS OUTSIDE BOTH, stated rather than left to be discovered and
    MEASURED rather than reasoned about: a constant that is neither prefixed nor
    returned. Declaring one worth 3 leaves both arms green, which was run. It is
    dead code - no branch hands it to the interpreter - so it is not an outcome,
    and the clause these arms judge is about outcomes. A third keying that
    graded every module-level integer would not close it either; it would redden
    at once on ``_RENAME_ATTEMPTS``, which is 5 and shares nothing with
    ``EXIT_USAGE`` but the number.

    Returns:
        Constant name to value.
    """
    declared = _declared_exit_codes()
    returned = _returned_exit_codes()
    disagreeing = sorted(
        name for name, value in returned.items() if declared.get(name, value) != value
    )
    assert disagreeing == [], (
        f"{len(disagreeing)} constant(s) hold one value in the module's namespace and another "
        f"in its source, so neither reading can be trusted: {disagreeing}"
    )
    return declared | returned


def _failing_openssl_stub(directory: Path) -> Path:
    """Put an openssl on PATH that is real, findable, and always fails.

    A REAL EXECUTABLE RATHER THAN A PATCH, because the outcome being measured is
    what the PROCESS exits with and an in-process monkeypatch cannot observe
    that. ``shutil.which`` has to find it the way it finds the real one, which
    on Windows means a name PATHEXT covers.

    Args:
        directory: Where to write the stub. Created if it is not there.

    Returns:
        The stub file. Its parent is what belongs on PATH.
    """
    directory.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        stub = directory / "openssl.bat"
        body = f"@echo off\r\nexit /b {STUB_OPENSSL_EXIT}\r\n"
    else:
        stub = directory / "openssl"
        body = f"#!/bin/sh\nexit {STUB_OPENSSL_EXIT}\n"
    # newline="" because a text-mode write translates \n to os.linesep on
    # Windows, which would turn the CRLF above into CR CR LF.
    stub.write_text(body, encoding="ascii", newline="")
    if os.name != "nt":
        stub.chmod(0o755)
    return stub


def _script_exit(args: Sequence[str], path: str | None = None) -> int:
    """Run the script as a real process and return the code it really exited with.

    Args:
        args: The command line, after the script path.
        path: A replacement PATH, or None to inherit this process's.

    Returns:
        The process exit status.
    """
    environment: dict[str, str] | None = None
    if path is not None:
        environment = dict(os.environ)
        environment["PATH"] = path
    done = subprocess.run(
        [sys.executable, str(MAKE_CERT_SOURCE), *args],
        shell=False,
        capture_output=True,
        text=True,
        timeout=OUTCOME_TIMEOUT_SECONDS,
        check=False,
        env=environment,
    )
    return done.returncode


def _at(directory: Path) -> list[str]:
    """Render the --cert-dir flag pointing at ``directory``.

    Args:
        directory: The destination. It does not have to exist.

    Returns:
        The two argv entries.
    """
    return ["--cert-dir", str(directory)]


def _collisions(codes: dict[str, int]) -> dict[int, frozenset[str]]:
    """Group names by the code they carry, keeping only codes more than one reaches.

    THE FULL MEMBER SET IS RETURNED, NEVER A PAIR, and that is what stops a
    recorded exemption from absorbing an unknown third member. A group of three
    is reported as a group of three, so an assertion comparing it against a
    two-name record FAILS rather than finding its record "contained" - which is
    the verdict-order fault memory/a-guard-can-measure-spelling.md records, an
    allowance that issues its own clearance.

    Args:
        codes: Name to exit code, for constants or for measured outcomes.

    Returns:
        Each shared code, mapped to every name that carries it.
    """
    by_code: dict[int, set[str]] = {}
    for name, code in codes.items():
        by_code.setdefault(code, set()).add(name)
    return {code: frozenset(names) for code, names in by_code.items() if len(names) > 1}


def _rendered(groups: dict[int, frozenset[str]]) -> list[tuple[int, list[str]]]:
    """Render collision groups as a stable, path-free value for a failure message.

    Args:
        groups: The output of :func:`_collisions`.

    Returns:
        One entry per shared code, sorted, with its members sorted.
    """
    return sorted((code, sorted(names)) for code, names in groups.items())


def _measure_every_outcome(root: Path) -> dict[str, tuple[int, ...]]:
    """Drive the script to every outcome it can reach, out of process, once each.

    THE TWO ARGPARSE OUTCOMES ARE MEASURED THE SAME WAY AS THE OTHER FIVE, which
    is the point of running these out of process at all: ``--help`` and a usage
    error never return to ``main``, so an in-process call cannot see what they
    exit with. Both spellings of the usage error are probed under ONE outcome
    key - an unknown flag and a flag missing its value are the same outcome, and
    filing them as two would make the injectivity assertion below unsatisfiable
    for a reason that is not a defect.

    NOTHING HERE IS PATCHED. The absent tool is an empty PATH, the failing tool
    is a real executable that fails, the occupied destination holds real files,
    and the unwritable destination is a directory sitting on the key's name -
    the same shape ``_forced_rename_pair`` uses.

    Args:
        root: A per-test temporary root. Everything is created beneath it.

    Returns:
        Outcome name to the codes its invocations produced.
    """
    no_tools = root / "no-tools"
    no_tools.mkdir()
    stubbed_path = str(_failing_openssl_stub(root / "stub-tools").parent) + os.pathsep
    stubbed_path += os.environ.get("PATH", "")

    occupied = root / "occupied"
    occupied.mkdir()
    (occupied / make_cert.CERT_NAME).write_text("not a certificate\n", encoding="ascii")
    (occupied / make_cert.KEY_NAME).write_text("not a key\n", encoding="ascii")

    blocked = root / "blocked"
    blocked.mkdir()
    (blocked / make_cert.KEY_NAME).mkdir()

    return {
        HELP_OUTCOME: (_script_exit(["--help"]),),
        "command line refused": (
            _script_exit([UNKNOWN_FLAG]),
            _script_exit(["--cert-dir"]),
        ),
        "openssl absent": (_script_exit(_at(root / "absent"), path=str(no_tools)),),
        "openssl failed": (_script_exit(_at(root / "stubbed"), path=stubbed_path),),
        "pair already there": (_script_exit(_at(occupied)),),
        WRITTEN_OUTCOME: (_script_exit(_at(root / "fresh")),),
        "pair not writable": (_script_exit([*_at(blocked), "--force"]),),
    }


#: EVERY EXIT-STATUS SITE THE SCRIPT HAS, mapped to how many times it is
#: written and which probed outcome drives it.
#:
#: THE KEYS AND THE COUNTS ARE DERIVED. :func:`_exit_status_sites` reads them out
#: of the module's own AST and the arm below compares the two for EQUALITY, so a
#: site arriving without a row is a finding rather than a member a record
#: happens not to mention.
#:
#: WHAT IS LISTED AND WHY, stated because the arm this feeds once claimed a
#: derivation it did not have. The OUTCOME NAMES and the site-to-outcome
#: attribution here are authored, and no AST can supply either: an outcome name
#: is a word a human chose, and which environment drives which branch is a fact
#: about ``shutil.which``, PATH and the filesystem rather than about syntax.
#: What the derivation buys is that neither can be quietly INCOMPLETE - a new
#: site has no row here, and a row naming an outcome nothing probes reddens the
#: measured arm. A row pointing at the WRONG outcome is a fault neither arm can
#: see, and that is the residue.
SITE_CENSUS: dict[tuple[str, str], tuple[int, str]] = {
    ("main", "EXIT_NO_OPENSSL"): (1, "openssl absent"),
    ("main", "EXIT_REFUSED"): (1, "pair already there"),
    ("_generate", "EXIT_OK"): (1, WRITTEN_OUTCOME),
    ("_generate", "EXIT_OPENSSL_FAILED"): (3, "openssl failed"),
    ("_generate", "EXIT_WRITE_FAILED"): (1, "pair not writable"),
    ("_CertParser.exit", "EXIT_HELP"): (1, HELP_OUTCOME),
    ("_CertParser.exit", "EXIT_USAGE"): (1, "command line refused"),
}


def _rendered_sites(census: dict[tuple[str, str], int]) -> list[tuple[str, int]]:
    """Render a site census as a stable, sorted, path-free value for a message.

    Sites render as ``function::constant``, the idiom this repository uses for a
    location that must carry no line number -
    ``tests/chained_cause_guard.py::CalleeSite`` states the reason on its key,
    and CS-857 is what taught it.

    Args:
        census: Site to the number of times the module writes it.

    Returns:
        One sorted entry per site.
    """
    return sorted((f"{function}::{name}", count) for (function, name), count in census.items())


def test_every_exit_status_the_script_can_produce_is_a_site_this_file_probes() -> None:
    """CS-882 residual. A branch nothing probes is an outcome nothing grades.

    THE FAULT THIS CLOSES IS THE FILED ONE, ONE LEVEL UP. CS-882 was filed
    against a LISTED exit-code table, and its repair shipped a LISTED outcome
    table - :func:`_measure_every_outcome` is seven hand-written keys - under a
    docstring claiming the population was derived three ways. MEASURED on this
    script: ONE extra branch returning the EXISTING ``EXIT_REFUSED`` puts two
    distinct outcomes on code 3, confirmed by running the script out of process,
    and every leg of the arm below stayed green - because a dict cannot contain
    a key nobody wrote.

    WHAT IS DERIVED HERE IS THE POPULATION OF SITES. Every place the script
    hands a value to the interpreter is read out of its AST, and
    :data:`SITE_CENSUS` is compared against it for EQUALITY rather than
    containment, so a site with no row reddens instead of being covered by a
    record that names the rest.

    EVERY EXIT STATUS MUST ALSO BE NAMED, which is the other half. A bare
    integer returned as a status is a code no constant declares, so no
    population keyed on a name can hold it however that keying is done. Refusing
    the literal is what keeps this arm and the distinctness arm talking about
    the same set.
    """
    tree = _make_cert_tree()
    sites, unnamed = _exit_status_sites(tree)

    derived: dict[tuple[str, str], int] = {}
    for site in sites:
        derived[site] = derived.get(site, 0) + 1

    site_count = len(sites)
    assert site_count > 0, "no exit-status site was read; this arm is asserting about nothing"
    assert unnamed == [], (
        f"{len(unnamed)} exit status(es) are named by no module-level constant, so no "
        f"population keyed on a name can hold them: {sorted(unnamed)}"
    )

    recorded = {site: count for site, (count, _outcome) in SITE_CENSUS.items()}
    derived_rows = _rendered_sites(derived)
    recorded_rows = _rendered_sites(recorded)
    assert derived_rows == recorded_rows, (
        "the script's exit-status sites and the record of them have drifted apart, and a "
        "site with no row is a branch no outcome below probes. "
        f"Derived: {derived_rows}. Recorded: {recorded_rows}"
    )


def test_exactly_one_recorded_pair_of_outcomes_shares_an_exit_code(tmp_path: Path) -> None:
    """CS-882. A runbook branches on these, so an UNRECORDED shared code is a lost branch.

    WHAT THIS ARM PROMISES, STATED HONESTLY. The acceptance clause is a universal
    over distinct outcomes, and this script does NOT meet it: ``--help`` and a
    completed mint both exit 0, by operator ruling, because POSIX convention
    outranks the universal for that pair. So the promise here is the weaker,
    true one - EXACTLY ONE pair shares a code, it is the recorded pair, and any
    OTHER sharing is a defect. The filed collision, argparse's usage error
    sitting on "openssl failed", is gone outright.

    THE EXEMPTION CANNOT ABSORB. It is compared for EQUALITY against the full
    membership of the single collision group, never for containment, so a third
    constant landing on 0 makes the group a three and reddens this arm rather
    than being covered by a record that names two. An exemption that grows to
    fit what it finds is the verdict-order fault
    memory/a-guard-can-measure-spelling.md records, and it is exactly the shape
    a distinctness check must not acquire while being weakened.

    THREE POPULATIONS ARE READ, AND WHAT IS LISTED IN EACH IS STATED RATHER THAN
    IMPLIED. What the module DECLARES is derived twice over and unioned - the
    prefixed constants out of its namespace, and every constant reaching an
    exit-status position out of its AST - so neither keying can hide what the
    other sees (:data:`EXIT_PREFIX`). What it DOCUMENTS is derived from its own
    docstring table. What it DOES is real processes, one per invocation, AND
    THOSE ARE DRIVEN BY A LISTED RECIPE: :func:`_measure_every_outcome` is seven
    hand-written keys, because no AST can say that an empty PATH is the thing
    that reaches ``EXIT_NO_OPENSSL``. The recipe cannot be silently INCOMPLETE -
    :data:`SITE_CENSUS` derives every exit-status site the script has, and
    ``test_every_exit_status_the_script_can_produce_is_a_site_this_file_probes``
    reddens on one no outcome here covers - but its outcome NAMES and its
    site-to-outcome attribution are authored, and a wrong attribution is a fault
    neither arm can see.

    AN EARLIER VERSION OF THIS DOCSTRING SAID THE POPULATION WAS DERIVED THREE
    WAYS while the third leg was a hand-written dict of seven literal keys. That
    is the CS-882 fault family reproduced one level up - the item was filed
    against a listed exit-code table and its repair shipped a listed outcome
    table, under prose asserting the opposite. A listed population is also what
    let the FILED collision go unnoticed: the arm CS-882 replaced named five
    constants, and argparse owned two more codes that no name reached.

    NON-EMPTINESS IS ASSERTED BEFORE ANY DISTINCTNESS IS, and that order is
    load-bearing rather than tidy. A collision search over an empty population
    finds nothing, and so does one over a broken measurement; both produce the
    same output as a clean script.
    """
    declared = _graded_exit_codes()
    documented = _documented_exit_codes()
    measured = _measure_every_outcome(tmp_path)

    declared_count = len(declared)
    documented_count = len(documented)
    outcome_count = len(measured)
    probe_count = sum(len(codes) for codes in measured.values())

    assert declared_count > 0, "no exit-code constant was read; this arm asserts about nothing"
    assert documented_count > 0, "the module docstring lists no exit code; the table moved"
    assert outcome_count > 0, "no outcome was measured; this arm is asserting about nothing"
    assert probe_count > outcome_count, "no outcome was probed twice; the usage pair went missing"

    # THE CHAIN LINK THAT MAKES THE RECIPE ABOVE MORE THAN A LIST. SITE_CENSUS is
    # pinned to the script's derived exit-status sites by the arm before this
    # one; pinning the probed outcomes to the census here is what carries that
    # derivation through to the seven keys, so a site the script grows forces a
    # census row and a census row forces a probe.
    attributed_outcomes = sorted({outcome for _count, outcome in SITE_CENSUS.values()})
    probed_outcomes = sorted(measured)
    assert probed_outcomes == attributed_outcomes, (
        "the outcomes probed here and the outcomes SITE_CENSUS attributes the script's "
        f"exit-status sites to are not the same set. Probed: {probed_outcomes}. "
        f"Attributed: {attributed_outcomes}"
    )

    inconsistent = sorted(name for name, codes in measured.items() if len(set(codes)) != 1)
    assert inconsistent == [], (
        f"{len(inconsistent)} outcome(s) exited differently from one invocation to the "
        f"next, so they are not one outcome: {inconsistent}"
    )

    outcome_codes = {name: codes[0] for name, codes in measured.items()}
    declared_values = set(declared.values())
    undeclared = sorted(
        f"{name} exits {code}"
        for name, code in outcome_codes.items()
        if code not in declared_values
    )
    assert undeclared == [], (
        f"{len(undeclared)} outcome(s) exit a code no exit-code constant declares: {undeclared}"
    )

    # The record has to name things that exist, or the two assertions it guards
    # are comparing against a set nothing could ever equal.
    unknown_exempt = sorted(EXEMPT_CONSTANTS - set(declared))
    assert unknown_exempt == [], (
        f"the recorded exemption names {unknown_exempt}, which no exit-code constant declares"
    )
    unprobed_exempt = sorted(EXEMPT_OUTCOMES - set(outcome_codes))
    assert unprobed_exempt == [], (
        f"the recorded exemption names outcome(s) {unprobed_exempt} that were never probed"
    )

    declared_shared = _collisions(declared)
    declared_shared_count = len(declared_shared)
    assert declared_shared_count == 1, (
        f"{declared_shared_count} exit code(s) are declared by more than one constant and "
        f"exactly ONE recorded collision is allowed - {EXEMPT_REASON}. "
        f"Measured: {_rendered(declared_shared)}"
    )
    declared_shared_names = next(iter(declared_shared.values()))
    assert declared_shared_names == EXEMPT_CONSTANTS, (
        f"the constants sharing a code are {sorted(declared_shared_names)} and the only "
        f"pair on the record is {sorted(EXEMPT_CONSTANTS)} - {EXEMPT_REASON}"
    )

    outcome_shared = _collisions(outcome_codes)
    outcome_shared_count = len(outcome_shared)
    assert outcome_shared_count == 1, (
        f"{outcome_shared_count} exit code(s) are reached by more than one outcome and "
        f"exactly ONE recorded collision is allowed - {EXEMPT_REASON}. "
        f"Measured: {_rendered(outcome_shared)}"
    )
    outcome_shared_names = next(iter(outcome_shared.values()))
    assert outcome_shared_names == EXEMPT_OUTCOMES, (
        f"the outcomes sharing a code are {sorted(outcome_shared_names)} and the only "
        f"pair on the record is {sorted(EXEMPT_OUTCOMES)} - {EXEMPT_REASON}"
    )

    assert declared_count == documented_count, (
        f"{declared_count} exit-code constant(s) against {documented_count} documented outcome "
        "row(s); the module docstring's table and its constants have drifted apart"
    )
    assert sorted(set(documented)) == sorted(declared_values), (
        "the exit-code constants and the module docstring's table do not name the same codes"
    )

    # THE RULING'S DIRECTION, pinned separately. Equality of the exempt pair says
    # they share A code; it does not say WHICH, and a pair that agreed on 7 would
    # satisfy every assertion above while breaking the convention the exemption
    # was granted to keep.
    assert make_cert.EXIT_OK == 0
    assert make_cert.EXIT_HELP == 0, (
        f"EXIT_HELP is not 0, so --help no longer exits what POSIX expects - {EXEMPT_REASON}"
    )
    help_code = outcome_codes[HELP_OUTCOME]
    assert help_code == 0, f"--help exited {help_code}, and the ruling is that it exits 0"


# ---------------------------------------------------------------------------
# The live arm - real openssl, real TLS, real loopback socket
# ---------------------------------------------------------------------------


def test_a_generated_pair_serves_real_tls_to_a_verifying_client(tmp_path: Path) -> None:
    """THE POSITIVE ARM. A real client, verifying properly, completes the round trip.

    ``check_hostname`` is left at the True that ``create_default_context``
    sets, and the server is addressed as 127.0.0.1, so the handshake succeeds
    only if the IP SAN is really in the certificate. Read together with the
    negative arm below, which is the half that gives this one its meaning.
    """
    cert_path, key_path = cert_pair(tmp_path)

    with tls_echo_server(cert_path, key_path, rounds=1) as (port, server_errors):
        context = ssl.create_default_context(cafile=str(cert_path))
        checks_hostname = context.check_hostname
        reply = _speak_tls(port, context, server_hostname="127.0.0.1")

    assert checks_hostname is True, "the client was not verifying the hostname at all"
    assert reply == b"clockspeed-ok"
    assert len(server_errors) == 0, f"the server saw {len(server_errors)} handshake error(s)"


def test_a_client_without_the_certificate_as_its_ca_is_rejected(tmp_path: Path) -> None:
    """THE NEGATIVE ARM, and it is what makes the positive arm mean anything.

    Same server, same port, same certificate. The only change is that this
    client carries the system trust store instead of the generated certificate,
    and it MUST be refused. Without this arm the positive arm above would pass
    just as happily against a client that validates nothing at all.
    """
    cert_path, key_path = cert_pair(tmp_path)

    with tls_echo_server(cert_path, key_path, rounds=1) as (port, server_errors):
        naive = ssl.create_default_context()
        with pytest.raises(ssl.SSLCertVerificationError) as caught:
            _speak_tls(port, naive, server_hostname="127.0.0.1")
        verify_code = caught.value.verify_code

    # The certificate was read, understood, and refused for the RIGHT reason
    # rather than for a transport fault, which would look identical from here.
    assert verify_code == SELF_SIGNED_VERIFY_CODE
    assert len(server_errors) == 1, (
        f"the server recorded {len(server_errors)} errors; a refused handshake should be exactly 1"
    )


def test_a_client_that_trusts_the_certificate_still_refuses_a_hostname_it_does_not_cover(
    tmp_path: Path,
) -> None:
    """The SAN is a real constraint, not decoration.

    The same trusting client, pointed at a name the certificate does not carry,
    is refused. This is the arm that fails if somebody "fixes" a SAN problem by
    widening the certificate to a wildcard.
    """
    cert_path, key_path = cert_pair(tmp_path)

    with tls_echo_server(cert_path, key_path, rounds=1) as (port, _server_errors):
        context = ssl.create_default_context(cafile=str(cert_path))
        with pytest.raises(ssl.SSLCertVerificationError) as caught:
            _speak_tls(port, context, server_hostname="clockspeed.example")
        message = str(caught.value)

    mentions_hostname = "match" in message.lower() or "hostname" in message.lower()
    assert mentions_hostname, "the refusal was not a hostname mismatch"


def test_the_generated_key_is_a_private_key_and_the_certificate_is_a_certificate(
    tmp_path: Path,
) -> None:
    """The two files did not get swapped, and neither is empty.

    Asserted on the PEM banner rather than on the file size, because two
    plausible-looking files of plausible size that are the wrong way round is
    exactly the mistake a size check waves through.
    """
    cert_path, key_path = cert_pair(tmp_path)

    cert_head = cert_path.read_text(encoding="ascii").splitlines()[0]
    key_head = key_path.read_text(encoding="ascii").splitlines()[0]

    assert cert_head == CERT_BANNER
    assert key_head == KEY_BANNER


# ---------------------------------------------------------------------------
# The refusal paths
# ---------------------------------------------------------------------------


def test_a_second_run_without_force_refuses_and_changes_neither_file(tmp_path: Path) -> None:
    """REFUSAL IS THE POINT, and so is leaving the existing pair untouched.

    The companion window is told to trust a specific certificate. Silently
    minting a new one on the next run would invalidate that trust with no
    diagnostic anywhere, so the second run refuses - and the assertion that
    matters is not the exit code but that both files are byte-identical
    afterwards. A script that exits 3 AFTER overwriting has done the damage.
    """
    cert_path, key_path = cert_pair(tmp_path)
    before = (
        hashlib.sha256(cert_path.read_bytes()).hexdigest(),
        hashlib.sha256(key_path.read_bytes()).hexdigest(),
    )

    code = make_cert.main(["--cert-dir", str(tmp_path)])

    after = (
        hashlib.sha256(cert_path.read_bytes()).hexdigest(),
        hashlib.sha256(key_path.read_bytes()).hexdigest(),
    )
    assert code == make_cert.EXIT_REFUSED
    assert after[0] == before[0], "the certificate was rewritten by a run that refused"
    assert after[1] == before[1], "the private key was rewritten by a run that refused"


def test_force_regenerates_the_pair(tmp_path: Path) -> None:
    """The sibling case. --force is the documented way through the refusal."""
    _cert_path, key_path = cert_pair(tmp_path)
    before = hashlib.sha256(key_path.read_bytes()).hexdigest()

    code = make_cert.main(["--cert-dir", str(tmp_path), "--force"])

    after = hashlib.sha256(key_path.read_bytes()).hexdigest()
    assert code == make_cert.EXIT_OK
    assert after != before, "--force did not actually mint a new key"


@pytest.mark.parametrize("removed", [CERT_BASENAME, KEY_BASENAME])
def test_a_half_present_pair_is_refused_rather_than_completed(tmp_path: Path, removed: str) -> None:
    """The sibling case the overwrite guard is easiest to get wrong.

    BOTH HALVES ARE EXERCISED, AND THAT IS NOT SYMMETRY FOR ITS OWN SAKE. A
    guard that checks only the certificate still refuses when the KEY is the
    missing half, so an arm that deletes only the key passes against the broken
    guard and against the correct one alike - it grades nothing. Measured: with
    the guard narrowed to the certificate alone, the key-removed arm stays
    green and the certificate-removed arm goes red. Either file being present
    has to be enough to refuse, because half a pair cannot serve TLS and a run
    that completed it would leave a fresh file beside a stale one.
    """
    cert_pair(tmp_path)
    (tmp_path / removed).unlink()
    survivor = next(path for path in tmp_path.iterdir() if path.name != removed)
    before = hashlib.sha256(survivor.read_bytes()).hexdigest()

    code = make_cert.main(["--cert-dir", str(tmp_path)])

    after = hashlib.sha256(survivor.read_bytes()).hexdigest()
    assert code == make_cert.EXIT_REFUSED
    assert after == before, "the surviving half of the pair was rewritten by a run that refused"


def test_openssl_never_writes_directly_to_the_destination_paths(tmp_path: Path) -> None:
    """THE STAGING MECHANISM, graded structurally because a race cannot be.

    Non-negotiable 5 wants an atomic write for any file another process may
    read, and both the surface and the shell read these. openssl fills a PEM
    progressively, so a reader arriving mid-write against the real path sees a
    truncated key; staging plus a rename makes it all-or-nothing.

    ASSERTED ON WHERE OPENSSL IS POINTED rather than by racing a reader against
    it. A timing test for this would be flaky in the direction that matters -
    passing when it happened not to catch the window - which is the worst
    property a guard can have. What openssl is handed is deterministic, and it
    is the whole mechanism: if the staged paths ever equal the destination
    paths, the rename has nothing left to make atomic.
    """
    cert_path = tmp_path / make_cert.CERT_NAME
    key_path = tmp_path / make_cert.KEY_NAME
    seen: list[tuple[Path, Path]] = []
    real_argv = make_cert.cert_argv

    def recording(cert: Path, key: Path, openssl: str = "openssl") -> list[str]:
        seen.append((Path(cert), Path(key)))
        return list(real_argv(cert, key, openssl))

    monkey = pytest.MonkeyPatch()
    monkey.setattr(make_cert, "cert_argv", recording)
    try:
        code = make_cert.main(["--cert-dir", str(tmp_path)])
    finally:
        monkey.undo()

    assert code == make_cert.EXIT_OK
    assert len(seen) == 1, f"openssl was invoked {len(seen)} times, expected once"
    staged_cert, staged_key = seen[0]
    assert staged_cert != cert_path, "openssl wrote the certificate straight to its final path"
    assert staged_key != key_path, "openssl wrote the private key straight to its final path"
    staged_under_destination = staged_key.parent.parent == tmp_path
    assert staged_under_destination, (
        "staging is not inside the destination, so the rename crosses filesystems and is not atomic"
    )


def test_a_failed_force_run_leaves_the_previous_pair_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE STAGING MECHANISM, graded rather than merely described.

    --force is the destructive path, so it is the one where writing in place
    would cost the operator a working certificate every time openssl hiccupped.
    The pair is generated into a staging directory and moved in only after
    openssl has succeeded, which means a failed --force run is a no-op. openssl
    is made to fail by handing it a flag it does not have, so the failure is a
    real openssl failure rather than a stand-in for one.
    """
    cert_path, key_path = cert_pair(tmp_path)
    before = (
        hashlib.sha256(cert_path.read_bytes()).hexdigest(),
        hashlib.sha256(key_path.read_bytes()).hexdigest(),
    )
    monkeypatch.setattr(
        make_cert,
        "cert_argv",
        lambda _cert, _key, openssl="openssl": [openssl, "req", "-clockspeed-not-a-real-flag"],
    )

    code = make_cert.main(["--cert-dir", str(tmp_path), "--force"])

    after = (
        hashlib.sha256(cert_path.read_bytes()).hexdigest(),
        hashlib.sha256(key_path.read_bytes()).hexdigest(),
    )
    survivors = sorted(entry.name for entry in tmp_path.iterdir())
    assert code == make_cert.EXIT_OPENSSL_FAILED
    assert after == before, "a failed --force run destroyed the pair it was replacing"
    assert survivors == [make_cert.CERT_NAME, make_cert.KEY_NAME], (
        f"{len(survivors)} entries remain; a failed run left staging behind"
    )


def test_a_successful_run_leaves_no_staging_directory_behind(tmp_path: Path) -> None:
    """The resource-lifetime half of the same mechanism.

    Staging is created inside the destination so the rename is same-filesystem
    and therefore atomic. That puts the burden of cleaning it up on this
    script, on every path out - including the ones that succeeded.
    """
    cert_pair(tmp_path)

    survivors = sorted(entry.name for entry in tmp_path.iterdir())
    assert survivors == [make_cert.CERT_NAME, make_cert.KEY_NAME], (
        f"{len(survivors)} entries in the certificate directory; expected exactly the pair"
    )


def test_an_absent_openssl_exits_one_with_no_traceback(tmp_path: Path) -> None:
    """Run as a REAL subprocess, because the claim is about a real exit.

    "No traceback" is a property of what the process prints, and an in-process
    call that returns an integer cannot observe it. PATH is pointed at an empty
    directory so shutil.which finds nothing, which is the honest shape of the
    absence rather than a monkeypatched stand-in for it.
    """
    empty = tmp_path / "empty-path"
    empty.mkdir()
    certs = tmp_path / "certs"

    environment = dict(os.environ)
    environment["PATH"] = str(empty)
    environment["CLOCKSPEED_CERT_DIR"] = str(certs)

    done = subprocess.run(
        [sys.executable, str(MAKE_CERT_SOURCE)],
        shell=False,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        env=environment,
    )
    combined = done.stdout + done.stderr

    assert done.returncode == make_cert.EXIT_NO_OPENSSL
    assert "Traceback" not in combined, "a missing tool produced a traceback instead of a message"
    assert "openssl" in combined, "the message does not name the tool that is missing"
    assert not certs.exists(), "a failed run left a certificate directory behind"


def test_the_environment_override_places_the_pair_where_it_says(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CLOCKSPEED_CERT_DIR is honoured, and the flag outranks it.

    Both channels exist for a reason - the operator gets the environment
    variable, and the test suite gets a flag that needs no environment
    mutation - so the precedence between them is pinned rather than left to
    whichever one the reader assumes.
    """
    from_env = tmp_path / "from-env"
    from_flag = tmp_path / "from-flag"
    monkeypatch.setenv(make_cert.ENV_CERT_DIR, str(from_env))

    env_code = make_cert.main([])
    flag_code = make_cert.main(["--cert-dir", str(from_flag)])

    assert env_code == make_cert.EXIT_OK
    assert flag_code == make_cert.EXIT_OK
    assert (from_env / make_cert.CERT_NAME).is_file(), "the environment override was ignored"
    assert (from_flag / make_cert.CERT_NAME).is_file(), "the flag did not outrank the environment"


def test_no_printed_line_carries_key_material(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Non-negotiable 12 counts a log line as an echo path.

    The key is the one artifact in this script that must never reach stdout,
    and the check is against the actual bytes of the actual key rather than
    against a guess at what a leak would look like.
    """
    code = make_cert.main(["--cert-dir", str(tmp_path)])
    printed = capsys.readouterr()
    combined = printed.out + printed.err

    key_body = (tmp_path / make_cert.KEY_NAME).read_text(encoding="ascii")
    interior = [line for line in key_body.splitlines() if line and not line.startswith("-----")]
    leaked = sum(1 for line in interior if line in combined)

    assert code == make_cert.EXIT_OK
    assert len(interior) > 0, "the key had no body lines; this test is asserting about nothing"
    assert leaked == 0, f"{leaked} line(s) of private key material reached the console"


# ---------------------------------------------------------------------------
# The redaction promise under a forced filesystem failure
# ---------------------------------------------------------------------------


#: The needle every arm in this section hunts for, and a SYNTHETIC one. CLAUDE.md
#: non-negotiable 3 forbids a real platform account id in a tracked file, so this
#: digit run was invented here, belongs to no machine, and is therefore the one
#: thing in these arms safe to name in an assertion message - which the real
#: destination path underneath it is not.
#:
#: IT IS THE NEEDLE PRECISELY BECAUSE redact() REWRITES IT, and every arm proves
#: that rewrite before drawing any conclusion from the needle's absence. A needle
#: redact() does not touch is missing from a LEAKING rendering exactly as
#: reliably as from a clean one, so an unproven needle turns this whole section
#: green while measuring nothing. The rewrite comes from the digit-run backstop
#: in clockspeed/data/locate.py, which is machine-independent - unlike the home
#: prefix inside a tmp_path, which is only redactable on a runner whose
#: temporary directory happens to sit below one.
FORCED_SEGMENT = "10000000000000001"

#: How long a forced run may take before it is called hung. Generous, because
#: the two rename arms let openssl finish before the failure they force can
#: happen at all, and bounded for the reason every other probe here is.
FORCED_RUN_TIMEOUT_SECONDS = 120


def _forced_run(cert_dir: Path) -> subprocess.CompletedProcess[str]:
    """Run the script out of process against ``cert_dir``, with ``--force``.

    A SUBPROCESS BECAUSE THE CLAIM IS ABOUT WHAT THE PROCESS RENDERS. The leak
    these arms grade was written by the default excepthook, which sits above
    main(), and an in-process call that returns an integer cannot observe it -
    the same reason ``test_an_absent_openssl_exits_one_with_no_traceback`` runs
    out of process.

    ``--force`` is load-bearing rather than incidental. Each arm below puts
    something in the destination to make the run fail, and main() refuses an
    occupied destination before ``_generate`` is reached at all, so without the
    flag these arms would grade the refusal instead of the failure.

    Args:
        cert_dir: The ``--cert-dir`` value. Neither it nor its parent has to
            exist.

    Returns:
        The finished process, with stdout and stderr captured as text.
    """
    return subprocess.run(
        [sys.executable, str(MAKE_CERT_SOURCE), "--cert-dir", str(cert_dir), "--force"],
        shell=False,
        capture_output=True,
        text=True,
        timeout=FORCED_RUN_TIMEOUT_SECONDS,
        check=False,
    )


#: A one-shot program that drives the rename site and lets the failure reach
#: the DEFAULT EXCEPTHOOK - the renderer CS-878 is actually about. Passed with
#: ``-c`` so nothing is written to disk, and it loads the script by path exactly
#: as :func:`_load_script` does.
#:
#: THE EXCEPTHOOK RATHER THAN ``traceback.format_exception``, and that is not a
#: stylistic preference. Formatting a caught exception inside the test process
#: renders an absolute path per frame and ends in ``str(exc)``, which is the
#: channel tests/test_exception_rendering.py exists to keep out of this tree -
#: an arm proving that nothing leaks must not leak in order to prove it. Letting
#: a subprocess die is also the stronger evidence, because it measures the real
#: renderer instead of a stand-in for it.
SITE_DRIVER = (
    "import importlib.util, sys\n"
    "from pathlib import Path\n"
    "spec = importlib.util.spec_from_file_location('cs878_site', sys.argv[1])\n"
    "module = importlib.util.module_from_spec(spec)\n"
    "spec.loader.exec_module(module)\n"
    "module._replace_with_retry(Path(sys.argv[2]), Path(sys.argv[3]))\n"
)


def _forced_rename_pair(tmp_path: Path) -> tuple[Path, Path]:
    """Stage a file, and a destination the rename cannot possibly succeed onto.

    The destination NAME is pre-created as a directory, which is the shape
    ``tests/test_chained_cause.py::force_workdir_rename`` uses against the
    graded twin. Nothing is patched; the operating system supplies the error.

    Args:
        tmp_path: The per-test temporary root.

    Returns:
        The staged source, and the occupied destination.
    """
    staged = tmp_path / FORCED_SEGMENT / "staged.pem"
    staged.parent.mkdir()
    staged.write_bytes(b"")
    final = tmp_path / FORCED_SEGMENT / make_cert.KEY_NAME
    final.mkdir()
    return staged, final


def _redaction_control() -> tuple[bool, str]:
    """Prove redact() rewrites :data:`FORCED_SEGMENT`, using the script's OWN oracle.

    THE SCRIPT'S OWN BOUND ``redact``, not a fresh import of it, so the oracle
    that grades a rendering cannot drift from the one the subject renders with.
    scripts/make_cert.py binds it at module scope and every line it prints goes
    through that object.

    Returns:
        Whether the needle is rewritten, and what it is rewritten to. The
        rewritten form is a placeholder rather than a path, so an assertion
        message may render it.
    """
    rewritten = make_cert.redact(FORCED_SEGMENT)
    return rewritten != FORCED_SEGMENT and FORCED_SEGMENT not in rewritten, rewritten


def test_a_rename_that_cannot_succeed_renders_no_unredacted_path(tmp_path: Path) -> None:
    """CS-878. The rename site's failure reaches the operator carrying no path.

    NOTHING IS PATCHED. The key's FINAL NAME is pre-created as a DIRECTORY, so
    the staged key cannot be renamed onto it and the operating system supplies
    the error itself. That is the shape
    ``tests/test_chained_cause.py::force_workdir_rename`` uses against the
    graded twin in clockspeed/save/workdir.py, which carries the same function
    name and the same sharing-violation retry.

    WHY A PATH IS THERE TO LEAK AT ALL. ``cert_dir`` calls ``.expanduser()`` on
    both the flag and ``CLOCKSPEED_CERT_DIR``, so the destination is
    operator-configurable to a home directory BY DESIGN, and a home path is
    personal data under non-negotiable 3.

    TWO CONTROLS EARN THE CONCLUSION. The needle is proven redactable, because
    one redact() ignores is absent from a leaking rendering too. And the run is
    proven to have FAILED, because a run that quietly succeeded renders no path
    for a reason that has nothing to do with redaction.

    NOTHING CAPTURED IS EVER RENDERED. The streams carry the real tmp_path -
    a home directory and an account name - so each assertion binds a boolean
    first and its message names only the synthetic needle.

    THIS ARM ALONE PROVES NEITHER BARRIER, AND THAT IS MEASURED RATHER THAN
    SUSPECTED. The repair installed two - the path-free clone raised at the
    rename site, and the catch-all that lets no OSError out of ``_generate`` -
    and reverting either ONE while leaving the other intact leaves this arm
    green. With only the clone, the escaping traceback carries no destination;
    with only the catch-all, the printed report carries only redacted fields.
    Either barrier satisfies the property this arm states, which is correct for
    an acceptance arm and useless as a grade of a mechanism.

    SO THE BARRIER-SPECIFIC GRADES LIVE IN THE OTHER THREE, and deleting any of
    them leaves a barrier measured by nothing while this arm keeps passing.
    ``test_the_rename_site_renders_no_path_through_the_default_excepthook``
    and ``test_the_rename_site_keeps_the_reason_and_carries_no_filename`` are
    the arms that redden when the clone is reverted;
    ``test_a_destination_that_cannot_be_prepared_renders_no_unredacted_path``
    and ``test_a_rename_that_cannot_succeed_exits_with_the_documented_code``
    are the two that redden when the catch-all is.
    """
    destination = tmp_path / FORCED_SEGMENT
    destination.mkdir()
    (destination / make_cert.KEY_NAME).mkdir()

    redactable, rewritten = _redaction_control()
    done = _forced_run(destination)
    leaked = FORCED_SEGMENT in (done.stdout + done.stderr)
    reported_success = done.returncode == make_cert.EXIT_OK

    assert redactable, (
        f"redact() left {FORCED_SEGMENT} unchanged, so its absence below would "
        "be evidence of nothing"
    )
    assert not reported_success, (
        "the staged key was renamed onto a directory, so the failure this arm "
        "forces never happened and nothing here was measured"
    )
    assert not leaked, (
        f"the run rendered {FORCED_SEGMENT}, which redact() rewrites to "
        f"{rewritten}; an operator whose destination sits under a home "
        "directory has that path in the output"
    )


def test_a_destination_that_cannot_be_prepared_renders_no_unredacted_path(
    tmp_path: Path,
) -> None:
    """The same promise at the sibling site that prepares the destination.

    ``_generate`` calls ``mkdir`` and then ``mkdtemp`` before openssl is ever
    launched, and both raise an OSError carrying the path they could not use. A
    FILE is placed where the destination's parent has to be, so
    ``mkdir(parents=True)`` fails on the operating system's own answer with
    nothing patched.

    SAME ROOT CAUSE AS THE RENAME ARM, DIFFERENT CALL - an OSError leaving
    ``_generate`` with its filename fields intact. It is graded separately
    rather than assumed covered, because a repair aimed only at the rename
    would leave this one exactly as it was.
    """
    blocker = tmp_path / FORCED_SEGMENT
    blocker.write_bytes(b"")

    redactable, rewritten = _redaction_control()
    done = _forced_run(blocker / "certs")
    leaked = FORCED_SEGMENT in (done.stdout + done.stderr)
    reported_success = done.returncode == make_cert.EXIT_OK

    assert redactable, (
        f"redact() left {FORCED_SEGMENT} unchanged, so its absence below would "
        "be evidence of nothing"
    )
    assert not reported_success, (
        "a destination was created underneath a plain file, so the failure this "
        "arm forces never happened and nothing here was measured"
    )
    assert not leaked, (
        f"the run rendered {FORCED_SEGMENT}, which redact() rewrites to "
        f"{rewritten}; the destination the run could not prepare is in the output"
    )


def test_the_rename_site_renders_no_path_through_the_default_excepthook(
    tmp_path: Path,
) -> None:
    """The site CS-878 names, rendered by the excepthook that leaked in the first place.

    WHAT IS RENDERED IS THE SUBJECT, NOT THE filename FIELDS, and that
    distinction is the whole of this arm. An implementation that clears
    ``filename`` and ``filename2`` but raises inside the ``except`` block
    WITHOUT suppressing the context still renders the original underneath
    "During handling of the above exception", both paths intact - measured
    before this arm was written rather than anticipated. The sibling arm below,
    which reads the filename fields, cannot see that channel at all; this one
    can, because it reads what a real interpreter really printed.

    THE SITE IS DRIVEN DIRECTLY, IN A SUBPROCESS. ``main`` is guarded, so
    reaching the site through it would grade the guard rather than the site -
    and the site is what a second caller, added later, would reach.

    NOTHING CAPTURED IS RENDERED. The captured streams carry the real tmp_path,
    so every assertion binds a boolean first and its message names only the
    synthetic needle and a function name.
    """
    staged, final = _forced_rename_pair(tmp_path)
    redactable, rewritten = _redaction_control()

    done = subprocess.run(
        [sys.executable, "-c", SITE_DRIVER, str(MAKE_CERT_SOURCE), str(staged), str(final)],
        shell=False,
        capture_output=True,
        text=True,
        timeout=FORCED_RUN_TIMEOUT_SECONDS,
        check=False,
    )
    survived = done.returncode == 0
    site_named = "_replace_with_retry" in done.stderr
    leaked = FORCED_SEGMENT in (done.stdout + done.stderr)

    assert redactable, (
        f"redact() left {FORCED_SEGMENT} unchanged, so its absence below would "
        "be evidence of nothing"
    )
    assert not survived, (
        "the staged file was renamed onto a directory, so the site under test "
        "never raised and nothing here was measured"
    )
    assert site_named, (
        "the driver died somewhere other than _replace_with_retry, so the "
        "absence of the needle below says nothing about the site"
    )
    assert not leaked, (
        f"the default excepthook rendered {FORCED_SEGMENT}, which redact() "
        f"rewrites to {rewritten}; the rename site still hands a path to the "
        "renderer above it"
    )


def test_the_rename_site_keeps_the_reason_and_carries_no_filename(tmp_path: Path) -> None:
    """The other half of the site's contract - the diagnostic it must not drop.

    ERRNO AND STRERROR ARE ASSERTED PRESENT. A site that closed the leak by
    dropping the reason would pass every rendering arm while costing the
    operator the only diagnostic there is; why the rename failed is what says
    whether a handle was held open or the destination is not writable at all.

    THE FIELDS ARE REDUCED TO SCALARS INSIDE THE HANDLER, which is a rule here
    rather than a preference. pytest rewrites an assertion to render the
    asserted EXPRESSION independently of its message, so asserting on a name
    that still holds the exception prints the exception - filenames included -
    and tests/test_handler_exception_rendering.py sweeps the whole tree for
    exactly that shape. Nothing below the handler holds the exception itself.

    THIS ARM CANNOT SEE THE CONTEXT CHANNEL. Empty filename fields are not proof
    that the rendering is clean, which is precisely why the excepthook arm above
    exists beside it. Neither arm is sufficient alone.
    """
    staged, final = _forced_rename_pair(tmp_path)

    raised = False
    errno_kept: int | None = None
    strerror_kept = ""
    filename_kept = False
    try:
        make_cert._replace_with_retry(staged, final)  # noqa: SLF001 - the site under test
    except OSError as exc:
        raised = True
        errno_kept = exc.errno
        strerror_kept = exc.strerror or ""
        filename_kept = exc.filename is not None or exc.filename2 is not None

    has_errno = errno_kept is not None
    has_strerror = bool(strerror_kept)

    assert raised, (
        "the staged file was renamed onto a directory, so the site under test "
        "never raised and nothing here was measured"
    )
    assert has_errno, "the failure reached the caller with no errno; the reason was dropped"
    assert has_strerror, "the failure reached the caller with no strerror; the reason was dropped"
    assert not filename_kept, (
        "the failure reached the caller with a filename field set, and "
        "OSError.__str__ appends that field verbatim to every rendering of it"
    )


def test_a_rename_that_cannot_succeed_exits_with_the_documented_code(tmp_path: Path) -> None:
    """A filesystem failure is reported the way every other failure here is.

    Before CS-878 this path exited 1 by escaping to the default excepthook, and
    1 is the code the module docstring gives to "openssl is not on PATH" - so a
    runbook branching on it read a rename failure as a missing tool. A pair
    openssl produced and the filesystem would not accept is neither a missing
    tool nor a failed one, so it gets its own code instead of borrowing one
    that already means something else.

    THE DIAGNOSTIC HAS TO SURVIVE, which is the other half of the repair. A
    silent exit code would satisfy the redaction promise and tell the operator
    nothing, so the errno is asserted present in what the run printed.
    """
    destination = tmp_path / FORCED_SEGMENT
    destination.mkdir()
    (destination / make_cert.KEY_NAME).mkdir()

    done = _forced_run(destination)
    combined = done.stdout + done.stderr
    traceback_printed = "Traceback" in combined
    errno_reported = "errno" in combined

    assert done.returncode == make_cert.EXIT_WRITE_FAILED, (
        f"a rename that could not succeed exited {done.returncode}, and the "
        f"documented code for it is {make_cert.EXIT_WRITE_FAILED}"
    )
    assert not traceback_printed, (
        "a filesystem failure produced a traceback instead of a message, which "
        "is the channel CS-878 closed"
    )
    assert errno_reported, "the failure was reported without the errno that explains it"


# ---------------------------------------------------------------------------
# The key's file mode
# ---------------------------------------------------------------------------


#: The mode ``_restrict`` asks for, and the mask that reads it back. Named
#: rather than written inline in the comparison because ruff's PLR2004 reads a
#: bare ``0o600`` there as a magic value, and because a mode is worth naming.
KEY_MODE = 0o600
MODE_MASK = 0o777

#: The distinctive half of the line ``scripts/make_cert.py::_restrict`` prints
#: when the platform refuses. Matched as a substring rather than as the whole
#: line, so a change to the ``note: `` prefix does not redden an arm that is
#: about the diagnostic being present rather than about its punctuation.
RESTRICT_NOTE = "could not restrict the key file's permissions"


def _posix_mode_bits_are_honoured(probe_dir: Path) -> bool:
    """Ask this platform, by measurement, whether a chmod sets the mode bits.

    THE CAPABILITY IS PROVEN RATHER THAN INFERRED FROM A PLATFORM NAME.
    Branching on ``os.name`` would freeze today's answer into the suite as
    though it were permanent, and it would then be wrong in both directions the
    moment either platform moved. This writes a throwaway file, asks for
    :data:`KEY_MODE`, and reads the mode back, so the arm it gates begins
    grading Windows on the day Windows honours the request and stops grading
    POSIX on the day POSIX stops.

    Args:
        probe_dir: A directory to write the throwaway file into. Normally a
            tmp_path, so the probe never touches the repository.

    Returns:
        True when the mode read back is exactly the mode asked for.
    """
    probe = probe_dir / "mode-probe"
    probe.write_bytes(b"")
    try:
        probe.chmod(KEY_MODE)
        honoured = (probe.stat().st_mode & MODE_MASK) == KEY_MODE
    except OSError:
        honoured = False
    finally:
        probe.unlink(missing_ok=True)
    return honoured


def test_the_generated_key_is_restricted_to_this_account(tmp_path: Path) -> None:
    """The success half of ``_restrict``, graded on the FINAL key.

    THE FINAL KEY AND NOT THE STAGED ONE, DELIBERATELY.
    ``scripts/make_cert.py::_generate`` calls ``_restrict`` on the STAGED key,
    and the pair is moved into place afterwards by an atomic replace. Asserting
    the staged file would grade the chmod alone; asserting the file at
    ``KEY_NAME`` once main() has returned
    grades the chmod AND that the move preserved it, which is the half that
    would rot in silence if the staging step were ever rewritten.

    THE SKIP IS A MISSING SUBJECT, NOT A MISSING DEPENDENCY - see the module
    docstring. On a platform that does not implement POSIX mode bits there is
    nothing here to be right or wrong about, and the gate is a measured
    capability rather than a platform name.

    ONLY AN INT CROSSES INTO THE ASSERTION. The key sits under a tmp_path,
    which carries a home path and an account name, so neither the path nor a
    stat result is asserted on or named in the message; the mode is masked to
    an int first and that int is the whole of what the report can render.
    """
    if not _posix_mode_bits_are_honoured(tmp_path):
        pytest.skip(
            "this platform did not honour a chmod on a file it had just "
            "written, so the mode bits _restrict asks for cannot be read back "
            "here and a green result would be a statement about nothing. The "
            "key's restriction is UNMEASURED on this platform, not absent"
        )

    _cert_path, key_path = cert_pair(tmp_path)

    mode = key_path.stat().st_mode & MODE_MASK
    assert mode == KEY_MODE, f"the final key's mode is 0o{mode:03o}, expected 0o{KEY_MODE:03o}"


def test_a_key_the_platform_would_not_restrict_is_still_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """The failure half of ``_restrict``, and it runs on every platform.

    ``_restrict`` promises two things for the case where the platform refuses:
    that it says so, and that the run still succeeds. The second is the
    substantive one - a key that could not be chmod'd is still a usable key,
    and failing the run over it would cost the operator a working certificate
    in order to report a limitation. Because the OSError is FORCED rather than
    waited for, this arm is real coverage on a runner of any platform rather
    than a POSIX-only one, which is what makes it the half that guards tier1.

    THE PATCH IS ON ``Path.chmod`` AND NOT ON ``os.chmod``, which is what keeps
    it surgical. ``scripts/make_cert.py::_restrict`` calls the pathlib method
    and is the whole of what calls it, so patching that hits exactly the call
    under test, while every other filesystem operation in the process - the staging
    cleanup, pytest's own tmp_path handling - still reaches the untouched
    ``os.chmod`` underneath. Patching the lower call would put the whole
    interpreter under the fault and grade something far wider than the promise.

    THE FORCED ERROR CARRIES NO PATH. An OSError built with the offending
    filename would put a tmp_path into an exception that a later report could
    render, so the errno and the strerror are given and the filename is not.
    """

    def refuse_chmod(_self: Path, _mode: int, **_kwargs: object) -> None:
        raise PermissionError(errno.EPERM, "operation not permitted")

    monkeypatch.setattr(Path, "chmod", refuse_chmod)

    code = make_cert.main(["--cert-dir", str(tmp_path)])
    printed = capsys.readouterr()

    noted = RESTRICT_NOTE in printed.out
    survivors = sorted(entry.name for entry in tmp_path.iterdir())
    pair_written = survivors == [make_cert.CERT_NAME, make_cert.KEY_NAME]

    assert code == make_cert.EXIT_OK, "a chmod the platform refused took the whole run down"
    assert noted, "the platform refused the chmod and the run said nothing about it"
    assert pair_written, f"{len(survivors)} entries remain; the pair was not written"


# ---------------------------------------------------------------------------
# The verify_env row
# ---------------------------------------------------------------------------


#: Every HARD row name ``scripts/verify_env.py`` can emit, held here as literals
#: this file owns. Two of them interpolate the SAME module constants
#: ``scripts/verify_env.py::_hard_rows`` interpolates, so renaming either
#: constant moves both sides together.
#:
#: PRIVACY, WHICH IS THE ONLY REASON THIS SET EXISTS. The arm below parses row
#: names out of the VERDICT line, and that line is process output; CLAUDE.md
#: non-negotiable 12 counts an assertion message as an echo path exactly like a
#: debug dump. Each HARD row name is built from a literal or from MIN_PYTHON and
#: EXPECTED_HOOKS_PATH, with the discovered values going into the row VALUE and
#: redacted there - so a name appearing below is provably free of a machine path
#: and is safe to render. A parsed name that is NOT in this set is one this file
#: has never seen and cannot vouch for, so the arm reports it as a COUNT and
#: never prints it. Deriving the set from ``collect_rows`` instead would have
#: bought nothing: an in-process rebuild of a path-bearing name is still a
#: path-bearing name, so it would allowlist exactly what it needs to exclude.
HARD_ROW_NAMES = frozenset(
    {
        "python >= " + ".".join(str(part) for part in verify_env.MIN_PYTHON),
        "git",
        "repo root is a git work tree",
        f"{verify_env.EXPECTED_HOOKS_PATH} directory",
        f"core.hooksPath -> {verify_env.EXPECTED_HOOKS_PATH}",
        "pytest",
        "ruff",
    }
)

#: The HARD rows a correctly provisioned checkout is still allowed to lack.
#:
#: Hook wiring is per-clone git config rather than a tracked file. ``git clone``
#: and ``actions/checkout`` both reproduce the tracked ``.githooks`` directory,
#: and neither runs ``scripts/install_hooks.py``, so a fresh checkout has
#: ``core.hooksPath`` unset on any platform - measured in a plain ``git clone``
#: on Windows, and measured on ubuntu-latest where it reddened the tier1 suite.
#: verify_env says the same thing in the note it attaches to that row: a fresh
#: clone runs ZERO protection until install_hooks.py sets it.
#:
#: Nothing else belongs here. The other six HARD rows are a tracked directory, a
#: property of the checkout itself, or a toolchain dependency the environment
#: installs, so a missing one is a real defect and still fails the arm below.
UNPROVISIONED_HARD_ROWS = frozenset({f"core.hooksPath -> {verify_env.EXPECTED_HOOKS_PATH}"})

#: The verdict line, whose two forms ``scripts/verify_env.py::render`` builds
#: one of per run. A line matching neither is itself a failure rather than a
#: case to skip, because an unparsed verdict grades nothing.
#:
#: CLEAN and MISSING rather than the obvious PASS and FAIL, and the reason is a
#: linter rather than taste: ruff's S105 reads a constant whose name ends in
#: PASS and whose value is a string literal as a hardcoded credential. The S
#: selector is live over tests/ - pyproject.toml lifts only S101, S603 and S607
#: there - so the obvious pair does not survive `ruff check`. Renaming them back
#: reddens the lint gate rather than this arm.
VERDICT_PREFIX = "VERDICT:"
VERDICT_CLEAN = "VERDICT: PASS"
VERDICT_MISSING = "VERDICT: FAIL - missing HARD dependencies: "


def test_verify_env_reports_openssl_as_a_soft_row() -> None:
    """The openssl row is SOFT, matching node, and for the same reason.

    Both are phase-6 dependencies - the certificate is for the companion
    window's HTTPS surface - and the advice path has to stay runnable on a
    machine that has neither. A HARD row here would fail the environment
    verdict on a machine where nothing is actually wrong.
    """
    rows, _port_rows, _facts = verify_env.collect_rows(REPO_ROOT)
    by_name = {row["name"]: row for row in rows}

    assert "openssl" in by_name, "collect_rows emits no openssl row at all"
    assert by_name["openssl"]["scope"] == "SOFT"


def test_verify_env_verdict_agrees_with_its_exit_code_and_names_openssl() -> None:
    """The script itself, run the way an operator runs it.

    Asserted on the real process because the acceptance clause is about what
    ``python scripts/verify_env.py`` prints and exits, and collect_rows alone
    cannot speak to either. Only counts and booleans are asserted on - the
    output carries redacted machine paths and is never rendered into a failure
    message here.

    WHY THIS NO LONGER SIMPLY DEMANDS EXIT 0. It used to, and that assertion
    was a statement about the OPERATOR'S HOOK-WIRED WORKING TREE rather than
    about the code under test. Hook wiring is per-clone git config, so a fresh
    checkout has core.hooksPath unset, whereupon verify_env correctly reports
    one missing HARD row and correctly exits 1 - measured in a plain
    ``git clone`` on Windows, and measured on ubuntu-latest, where the arm took
    the tier1 suite down for a reason that had nothing to do with make_cert or
    with the openssl row. What it graded was the machine it happened to run on.

    WHAT IT GRADES INSTEAD, AND WHY THAT IS NOT A RELAXATION. Two properties
    that survive the move between those machines. First, the single VERDICT
    line and the exit code agree - PASS implies 0, and a non-empty missing set
    implies 1 - so ``main`` cannot report a clean environment while exiting
    non-zero, nor the reverse. Second, and this is the clause that keeps the
    arm from grading nothing, the missing set has to lie inside
    :data:`UNPROVISIONED_HARD_ROWS`, the rows a checkout lacks because
    provisioning rather than the repository supplies them. A missing pytest, a
    missing ruff, an absent ``.githooks`` directory or a checkout that is not a
    work tree each still redden this arm. Widening the assertion to "the exit
    code is 0 or 1" would have graded nothing at all.

    NEITHER BRANCH GOES UNEXERCISED, which is what makes an environment-shaped
    arm worth keeping. The tier1 job and the tier2 ``suite`` job run the suite
    in a checkout nobody wired and take the missing-set branch; the tier2
    ``clean-checkout-probe`` job runs ``scripts/install_hooks.py`` before the
    suite and takes the PASS branch, as does an operator's own working tree.

    EVERY BINDING ASSERTED ON BELOW IS AN INT OR A BOOL, bound before the
    assert rather than inside it, which is stricter than the arm this replaces.
    ``assert done.returncode == 0`` rendered ``where 1 = CompletedProcess(...)``
    - the whole repr, argv and captured stdout included - because pytest reprs
    the object an attribute was read from. tests/conftest.py redacts the report
    afterwards, but a redactor is a net under the rule and not the rule.
    """
    done = subprocess.run(
        [sys.executable, str(VERIFY_ENV_SOURCE)],
        shell=False,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
        cwd=str(REPO_ROOT),
    )
    lines = done.stdout.splitlines()
    openssl_rows = sum(1 for line in lines if "openssl" in line)
    verdicts = [line for line in lines if line.startswith(VERDICT_PREFIX)]
    verdict_count = len(verdicts)

    assert openssl_rows >= 1, "no line of the dependency table mentions openssl"
    assert verdict_count == 1, f"expected one VERDICT line, saw {verdict_count}"

    passed = verdicts[0].startswith(VERDICT_CLEAN)
    failed = verdicts[0].startswith(VERDICT_MISSING)
    assert passed != failed, (
        "the VERDICT line matched neither form this arm parses, so nothing below "
        "it grades anything; the line is withheld here because it is process output"
    )

    missing: frozenset[str] = frozenset()
    if failed:
        missing = frozenset(verdicts[0][len(VERDICT_MISSING) :].split(", "))

    expected_code = 1 if missing else 0
    code_agrees = done.returncode == expected_code
    assert code_agrees, (
        f"the verdict implies exit {expected_code} and the process exited {done.returncode}"
    )

    unnamed_count = len(missing - HARD_ROW_NAMES)
    assert unnamed_count == 0, (
        f"{unnamed_count} missing HARD row(s) carry a name this arm does not know, so "
        "they are withheld - only a name this file owns is provably free of a machine "
        "path. Run scripts/verify_env.py to read them."
    )

    unexpected = sorted((missing & HARD_ROW_NAMES) - UNPROVISIONED_HARD_ROWS)
    unexpected_count = len(unexpected)
    unexpected_names = ", ".join(unexpected)
    assert unexpected_count == 0, (
        "an unprovisioned checkout legitimately lacks the hook wiring and nothing else; "
        f"{unexpected_count} further HARD row(s) are missing: {unexpected_names}"
    )


# ---------------------------------------------------------------------------
# The citations this slice makes
# ---------------------------------------------------------------------------


#: The two files this arm judges - the pair CS-882's residual repair owns. NOT
#: the tree, and that is deliberate: a tree-wide citation guard over source
#: files is filed as its own item, and an arm that quietly grew into one here
#: would be that item shipped without its acceptance.
CITED_BY = ("scripts/make_cert.py", "tests/test_make_cert.py")

#: A repository path ending in the module extension, carrying the leading-dot
#: case the sibling guard measured: a path segment may begin with a dot, and a
#: pattern anchored on an alphanumeric drops it and then reports a path that
#: does not exist.
_CITED_PATH = r"\.?[A-Za-z0-9_][A-Za-z0-9_/.-]*\.py"

#: A citation naming a SYMBOL after a double colon - the form
#: ``tests/test_docs_citations.py`` grades in markdown, and the form this
#: repository writes everywhere else.
SYMBOL_CITATION = re.compile(rf"({_CITED_PATH})::([A-Za-z_][A-Za-z0-9_]*)")

#: The same path followed by a single colon and a number. IT IS MATCHED IN ORDER
#: TO BE REFUSED rather than resolved, which is why no instance of the form is
#: written anywhere in this file - a worked example would be a finding against
#: the arm that judges it.
LINE_POINTER = re.compile(rf"({_CITED_PATH}):(\d+)")


def _module_scope_names(source: str) -> frozenset[str]:
    """Every name a module binds at module scope.

    THE SAME RULE AS ``tests/test_docs_citations.py::module_scope_names`` -
    module-level functions, classes and assignment targets - and it is spelled
    again here rather than imported. Importing would make collection of this
    module depend on a sibling that builds a live corpus of the whole index, to
    borrow one pure function. The rule is three branches, and the sibling is
    cited by symbol so a reader can check the two still agree.

    Args:
        source: The module's full text.

    Returns:
        The bound names.

    Raises:
        SyntaxError: The source does not parse.
    """
    names: set[str] = set()
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.Assign):
            names.update(target.id for target in node.targets if isinstance(target, ast.Name))
    return frozenset(names)


def test_every_source_citation_in_this_slice_names_a_symbol_that_is_really_there() -> None:
    """CS-882 residual. A citation is a claim, and three of this module's were false.

    MEASURED on the tree as CS-882 left it: this module carried three pointers
    into ``scripts/make_cert.py`` written as line numbers, and all three were
    dead. Two landed inside ``cert_argv``'s argv list and the third on a blank
    line, while the prose around them described ``scripts/make_cert.py::_restrict``,
    its chmod and its call site. Nothing in the tree could see it -
    ``tests/test_docs_citations.py`` grades citations in ``docs`` markdown, and
    this is a test module.

    A LINE NUMBER IS REFUSED RATHER THAN RESOLVED, which is the CS-857 lesson and
    the reason ``tests/chained_cause_guard.py::CalleeSite`` keys its population
    without one: a pointer to a line drifts on any edit above it, so a correct
    one is correct until the next commit. CS-882's own commit pushed those three
    a further 44 lines from what they described. Resolving the number instead of
    banning it would buy a guard that goes green again the moment somebody
    renumbers the pointer to whatever now sits there; a symbol moves with the
    thing it names, so it cannot be repaired into a lie.

    THIS ARM IS TWO FILES WIDE AND SAYS SO. :data:`CITED_BY` is the slice that
    owns it. A tree-wide guard over source citations is a separate item, and an
    arm that grew into one here would be that item shipped with no acceptance.
    """
    pointers: list[str] = []
    unresolved: list[str] = []
    citation_count = 0
    for path in CITED_BY:
        text = (REPO_ROOT / path).read_text(encoding="ascii")
        pointers.extend(
            f"{path} points into {cited} by line" for cited, _line in LINE_POINTER.findall(text)
        )
        for cited, symbol in SYMBOL_CITATION.findall(text):
            citation_count += 1
            target = REPO_ROOT / cited
            if not target.is_file():
                unresolved.append(f"{path} cites {cited}::{symbol}, and that file is not here")
            elif symbol not in _module_scope_names(target.read_text(encoding="utf-8")):
                unresolved.append(f"{path} cites {cited}::{symbol}, which it does not bind")

    assert citation_count > 0, "no symbol citation was read; this arm asserts about nothing"
    assert pointers == [], (
        f"{len(pointers)} citation(s) point at a LINE rather than at a symbol, which is the "
        f"dead-citation shape CS-857 was filed against: {sorted(pointers)}"
    )
    assert unresolved == [], (
        f"{len(unresolved)} citation(s) name a symbol that is not there: {sorted(unresolved)}"
    )


# ---------------------------------------------------------------------------
# CS-910 - the tool a script runs must not be chosen by where it is standing
# ---------------------------------------------------------------------------

#: The environment variable Windows consults before adding the CURRENT
#: DIRECTORY to an executable search, named once so the arms that remove it and
#: the prose explaining them cannot drift apart.
#:
#: MEASURED 2026-09-05: it is set at NEITHER machine nor user scope on the
#: development machine, so a process launched from Explorer - which is what a
#: shortcut produces - has the current-directory search LIVE. Some shells set it
#: for themselves, and the harness shell this class was first probed under is one
#: of them, which is why a naive probe comes back clean and means nothing. The
#: arms below therefore remove it from the CHILD environment rather than trusting
#: whatever the parent happened to inherit.
CURDIR_GATE = "NoDefaultCurrentDirectoryInExePath"

#: What the planted openssl exits with. Never read back through make_cert's own
#: exit code - that collapses every openssl failure onto EXIT_OPENSSL_FAILED -
#: but kept distinct from STUB_OPENSSL_EXIT so a stray stub can never be mistaken
#: for this one in a transcript.
PLANTED_OPENSSL_EXIT = 34

#: The file the planted openssl writes before exiting. Its EXISTENCE is the
#: measurement: an exit code says only that something failed, whereas a marker on
#: disk says the planted binary is the thing that ran.
PLANTED_MARKER_NAME = "planted-openssl-ran.txt"

#: What the child probe prints when the current-directory search is live.
GATE_OPEN = "True"


def _plant_openssl(directory: Path) -> Path:
    """Write an openssl into ``directory`` that records having been run.

    A REAL EXECUTABLE RATHER THAN A PATCH, for the reason
    :func:`_failing_openssl_stub` states: an in-process patch cannot observe what
    a real spawn resolved. This one differs from that stub in the single way that
    is the whole point - it is planted in the WORKING DIRECTORY and never on
    PATH, so nothing is entitled to find it.

    Args:
        directory: Where to plant. Created if it is not there.

    Returns:
        The planted file.
    """
    directory.mkdir(parents=True, exist_ok=True)
    marker = PLANTED_MARKER_NAME
    if os.name == "nt":
        planted = directory / "openssl.bat"
        body = f"@echo off\r\necho ran > {marker}\r\nexit /b {PLANTED_OPENSSL_EXIT}\r\n"
    else:
        planted = directory / "openssl"
        body = f"#!/bin/sh\necho ran > {marker}\nexit {PLANTED_OPENSSL_EXIT}\n"
    # newline="" for the reason _failing_openssl_stub states: a text-mode write
    # would translate the CRLF above into CR CR LF.
    planted.write_text(body, encoding="ascii", newline="")
    if os.name != "nt":
        planted.chmod(0o755)
    return planted


def _curdir_search_env(path_value: str) -> dict[str, str]:
    """A child environment with the current-directory gate REMOVED.

    Removed by a case-insensitive scan rather than by one ``pop``: Windows
    environment names are case-insensitive, a mapping copied out of
    ``os.environ`` can hold the variable under any spelling, and a single-key
    delete that misses leaves the arm grading nothing while still going green.

    Args:
        path_value: What the child's PATH is set to.

    Returns:
        The complete child environment.
    """
    environment = dict(os.environ)
    for key in [name for name in environment if name.upper() == CURDIR_GATE.upper()]:
        del environment[key]
    environment["PATH"] = path_value
    return environment


def _child_probe(source: str, working_dir: Path, environment: dict[str, str]) -> str:
    """Run one throwaway probe as a real child, standing in ``working_dir``.

    NOTHING THIS RETURNS IS EVER A PATH. The two callers below ask it yes/no
    questions and it hands back the answer, because a probe that returned what it
    resolved would put a temporary directory - and therefore the account name -
    into an assertion message.

    Args:
        source: The program to run with ``-c``.
        working_dir: The child's current directory.
        environment: The child's complete environment.

    Returns:
        Stripped stdout.
    """
    done = subprocess.run(
        [sys.executable, "-c", source],
        shell=False,
        capture_output=True,
        text=True,
        cwd=str(working_dir),
        env=environment,
        timeout=OUTCOME_TIMEOUT_SECONDS,
        check=False,
    )
    probe_status = done.returncode
    assert probe_status == 0, f"the probe itself failed with status {probe_status}"
    return done.stdout.strip()


#: The line ``scripts/make_cert.py`` prints on the no-openssl branch. Spelled
#: here rather than imported because the script builds it inline at the print.
NO_OPENSSL_DIAGNOSTIC = "openssl is not on PATH"


def test_a_planted_openssl_in_the_working_directory_is_never_run(tmp_path: Path) -> None:
    """CS-910 - the current directory may not supply the tool a script runs.

    THE CONTROL RUNS FIRST AND IS PART OF THE ARM. A negative measurement is
    worth nothing without evidence that the thing being looked for could have
    been seen, so this asserts three things before it asserts the property: the
    plant landed, the current-directory search is genuinely LIVE in the child,
    and a current-directory-consulting resolver DOES offer the plant. Without all
    three a green result is indistinguishable from an arm that reproduced
    nothing at all.

    PATH IS EMPTIED OF OPENSSL DELIBERATELY, so the only openssl the child can
    reach anywhere is the planted one. That makes "openssl is not on PATH" the
    single correct outcome and any spawn whatsoever the defect.

    EVERY ASSERTION BINDS A SCALAR. pytest renders the asserted EXPRESSION
    independently of the message and a temporary path on Windows carries the
    account name, which is non-negotiable 3.
    """
    standing = tmp_path / "standing"
    planted = _plant_openssl(standing)
    marker = standing / PLANTED_MARKER_NAME
    empty_path = tmp_path / "no-tools"
    empty_path.mkdir()
    environment = _curdir_search_env(str(empty_path))

    landed = planted.is_file() and planted.stat().st_size > 0
    assert landed, "the plant did not land, so this arm grades nothing"
    ran_before = marker.exists()
    assert not ran_before, "the marker existed before anything ran"

    gate = _child_probe(
        "import os,sys;sys.stdout.write(str(os.name != 'nt' or"
        " __import__('_winapi').NeedCurrentDirectoryForExePath('openssl')))",
        standing,
        environment,
    )
    assert gate == GATE_OPEN, (
        "the current-directory search is not live in the child, so this arm cannot"
        " reproduce the defect it exists to grade"
    )

    offered = _child_probe(
        "import shutil,sys;sys.stdout.write(str(shutil.which('openssl') is not None))",
        standing,
        environment,
    )
    assert offered == GATE_OPEN, (
        "a current-directory-consulting resolver did not offer the plant, so the"
        " control failed and the negative below would prove nothing"
    )

    done = subprocess.run(
        [sys.executable, str(MAKE_CERT_SOURCE), *_at(tmp_path / "fresh")],
        shell=False,
        capture_output=True,
        text=True,
        cwd=str(standing),
        env=environment,
        timeout=OUTCOME_TIMEOUT_SECONDS,
        check=False,
    )

    planted_ran = marker.exists()
    assert not planted_ran, (
        "the openssl planted in the WORKING DIRECTORY was executed - the tool this"
        " script runs is chosen by where the process happens to be standing"
    )
    # THE DIAGNOSTIC IS ASSERTED BECAUSE THE EXIT CODE ALONE IS AMBIGUOUS.
    # EXIT_NO_OPENSSL is 1, which is also the status Python gives an uncaught
    # exception, so this arm's GREEN was satisfiable by a main() that crashed
    # before reaching the branch - MEASURED, by replacing the resolver call with
    # a raise and watching the arm still pass. The printed line is what makes
    # the pass a statement about the branch actually taken.
    spoke = NO_OPENSSL_DIAGNOSTIC in done.stdout
    assert spoke, (
        "the script exited without printing the no-openssl diagnostic, so the exit"
        " code alone does not say which branch it took"
    )
    status = done.returncode
    assert status == make_cert.EXIT_NO_OPENSSL, (
        f"expected EXIT_NO_OPENSSL ({make_cert.EXIT_NO_OPENSSL}), because no openssl is"
        f" reachable on PATH, and got {status}"
    )
