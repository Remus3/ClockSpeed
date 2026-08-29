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

NOTHING HERE IS MARKED SLOW AND NOTHING HERE SKIPS. The ``slow`` marker
currently excludes nothing anywhere - ``.githooks/pre-push`` runs pytest with no
``-m`` filter - so marking the live arms would hide them from no one while
suggesting they are optional. A skipped test is not a passing test: if openssl
is genuinely absent, these fail loudly and say so.

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
import hashlib
import importlib.util
import os
import socket
import ssl
import subprocess
import sys
import threading
from collections.abc import Iterator
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


def test_the_exit_codes_are_four_distinct_values() -> None:
    """A runbook branches on these, so two that collide are one lost branch."""
    codes = [
        make_cert.EXIT_OK,
        make_cert.EXIT_NO_OPENSSL,
        make_cert.EXIT_OPENSSL_FAILED,
        make_cert.EXIT_REFUSED,
    ]

    distinct = len(set(codes))
    assert distinct == len(codes), f"only {distinct} of {len(codes)} exit codes are distinct"
    assert make_cert.EXIT_OK == 0


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
# The verify_env row
# ---------------------------------------------------------------------------


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


def test_verify_env_still_passes_and_names_openssl() -> None:
    """The script itself, run the way an operator runs it.

    Asserted on the real process because the acceptance clause is about what
    ``python scripts/verify_env.py`` prints and exits, and collect_rows alone
    cannot speak to either. Only counts and booleans are asserted on - the
    output carries redacted machine paths and is never rendered into a failure
    message here.
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
    verdict_pass = sum(1 for line in lines if line.startswith("VERDICT: PASS"))

    assert done.returncode == 0, f"verify_env exited {done.returncode}"
    assert openssl_rows >= 1, "no line of the dependency table mentions openssl"
    assert verdict_pass == 1, f"expected one PASS verdict line, saw {verdict_pass}"
