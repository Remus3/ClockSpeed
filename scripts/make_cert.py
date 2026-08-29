#!/usr/bin/env python3
"""Mint the self-signed certificate the local HTTPS dashboard listens with.

The dashboard serves on loopback only, so the certificate never leaves this
machine and no public authority is involved. What it still has to be is a
certificate a REAL client will accept without being told to stop checking -
which is why the subject alternative name carries the loopback ADDRESS as well
as the name. A client pointed at ``https://127.0.0.1:<port>`` with hostname
checking left on verifies against the IP SAN; without it the only way through
is ``check_hostname = False``, and a project that ships that has replaced a
certificate problem with a silent one.

WHY THIS SHELLS OUT. The Python standard library cannot generate a certificate,
and ``pyproject.toml`` declares ``dependencies = []`` and records that as a
decision (BOOTSTRAP.md section 11). Adding ``cryptography`` to mint one file is
not a trade this project makes, so openssl - already present on this machine as
part of the git toolchain - does the minting.

OPENSSL IS NEVER INVOKED THROUGH A SHELL, AND THAT IS MEASURED RATHER THAN
STYLISTIC. Through Git Bash, MSYS path conversion rewrites the bare
``/CN=clockspeed-local`` argument into an absolute Windows path before openssl
ever sees it, and openssl rejects the result. Every call below passes a list
argv with ``shell=False``, which is immune. A future reader hitting a quoting
problem must not "fix" it with ``shell=True``; tests/test_make_cert.py pins the
absence.

THE TOOL IS RESOLVED FROM PATH BY NAME. CLAUDE.md non-negotiable 3 forbids a
machine-specific absolute path in a tracked file, and where openssl lives
differs between the git toolchain, a system install and a package manager.

REFUSAL IS THE DEFAULT. The companion window is told to trust one specific
certificate, so quietly minting a replacement would invalidate that trust with
no diagnostic anywhere. An existing certificate or key - EITHER of them, since
half a pair cannot serve TLS - stops the run unless ``--force`` is given.

FILE PERMISSIONS, STATED HONESTLY. The key is chmod 0600 on the way out, which
is meaningful on POSIX and very nearly meaningless on Windows, where CPython's
``os.chmod`` only toggles the read-only attribute and does not touch the ACL
that actually governs access. This is recorded rather than papered over: on
Windows the real control is that ``.gitignore`` keeps the key out of the
repository, and that the key never leaves this machine. Do not read the chmod
call as a claim that the key is protected from other local accounts.

PRIVACY. ``CLOCKSPEED_CERT_DIR`` can point inside a home directory, and a home
path is personal data under non-negotiable 3. Every path this script prints -
including one arriving inside an openssl diagnostic - goes through redact()
first. Key material is never printed on any path.

Exit codes, distinct so a runbook can branch on them:

    0  the pair was written
    1  openssl is not on PATH
    2  openssl was found and failed, timed out, or produced nothing
    3  a pair is already there and --force was not given

Usage:
    python scripts/make_cert.py
    python scripts/make_cert.py --force
    python scripts/make_cert.py --cert-dir <directory>
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path

# Running a file puts that file's own directory on sys.path, not the repository
# root, so the package import below needs the insert. Same reasoning as
# scripts/verify_env.py, which states it at length.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from clockspeed.data.locate import redact  # noqa: E402

#: The certificate and its key, named so the pair is obvious in a listing.
CERT_NAME = "dashboard.cert.pem"
KEY_NAME = "dashboard.key.pem"

#: Overrides the default ``<repo root>/certs`` destination.
ENV_CERT_DIR = "CLOCKSPEED_CERT_DIR"

#: The default destination, relative to the repository root. ``.gitignore``
#: carries ``/certs/`` plus ``*.pem`` and ``*.key``, so nothing written here can
#: be committed by accident.
DEFAULT_CERT_DIRNAME = "certs"

#: Bounded, because an external probe that never returns hangs whatever called
#: it - the failure class CS-816 is open on. Key generation is a second or two;
#: this is a ceiling, not a budget.
OPENSSL_TIMEOUT_SECONDS = 120

#: 397 days is the maximum lifetime a public client will accept. Nothing public
#: will ever see this certificate, and the limit is kept anyway: a lifetime a
#: browser would reject is a trap waiting for the day the shell enforces one.
CERT_DAYS = "397"

#: The subject. A common name is required and is not what gets verified - the
#: subject alternative name below is.
CERT_SUBJECT = "/CN=clockspeed-local"

#: The extensions, in the order openssl receives them. THE SAN IS THE
#: LOAD-BEARING ONE and it carries both spellings of this machine: the name a
#: browser uses and the address the shell connects to.
CERT_EXTENSIONS = (
    "subjectAltName=DNS:localhost,IP:127.0.0.1",
    "basicConstraints=critical,CA:FALSE",
    "keyUsage=critical,digitalSignature,keyEncipherment",
    "extendedKeyUsage=serverAuth",
)

EXIT_OK = 0
EXIT_NO_OPENSSL = 1
EXIT_OPENSSL_FAILED = 2
EXIT_REFUSED = 3

#: os.replace can lose to a virus scanner or an open handle on Windows. A few
#: short retries turn a transient sharing violation into a completed rename.
_RENAME_ATTEMPTS = 5
_RENAME_PAUSE_SECONDS = 0.1


def cert_argv(cert_path: Path, key_path: Path, openssl: str = "openssl") -> list[str]:
    """Render the openssl command that mints the pair, without running it.

    PURE ON PURPOSE. Separating the argv from the execution is what lets the
    flags be asserted on a machine with no openssl installed at all, which is
    the machine the rule suite has to run on (BOOTSTRAP.md section 5.4). A
    version of this that only existed inside the runner could be graded only
    where openssl happens to be present.

    Args:
        cert_path: Where the certificate is written.
        key_path: Where the private key is written.
        openssl: The executable, resolved from PATH by the caller. Defaults to
            the bare name so this stays callable with nothing installed.

    Returns:
        The complete argv, ready for subprocess.run with shell=False.
    """
    argv = [
        openssl,
        "req",
        "-x509",
        "-newkey",
        "rsa:2048",
        "-sha256",
        "-days",
        CERT_DAYS,
        "-noenc",
        "-keyout",
        str(key_path),
        "-out",
        str(cert_path),
        "-subj",
        CERT_SUBJECT,
    ]
    for extension in CERT_EXTENSIONS:
        argv += ["-addext", extension]
    return argv


def cert_dir(explicit: str | None = None) -> Path:
    """Resolve where the pair belongs.

    Precedence is flag, then environment, then the default beside the
    repository - stated here rather than left to whichever the reader assumes.

    Args:
        explicit: The --cert-dir value, or None.

    Returns:
        The destination directory. Not created, and not required to exist.
    """
    if explicit:
        return Path(explicit).expanduser()
    declared = (os.environ.get(ENV_CERT_DIR) or "").strip()
    if declared:
        return Path(declared).expanduser()
    return _REPO_ROOT / DEFAULT_CERT_DIRNAME


def _replace_with_retry(source: Path, target: Path) -> None:
    """Move ``source`` onto ``target``, retrying a Windows sharing violation.

    Args:
        source: The staged file.
        target: Where it belongs.

    Raises:
        OSError: The rename kept failing.
    """
    for attempt in range(_RENAME_ATTEMPTS):
        try:
            source.replace(target)
        except PermissionError:
            if attempt == _RENAME_ATTEMPTS - 1:
                raise
            time.sleep(_RENAME_PAUSE_SECONDS)
        else:
            return


def _restrict(key_path: Path) -> None:
    """Ask the platform to keep the key to this account.

    Near-meaningless on Windows - see the module docstring - and never fatal.
    A key that was written but could not be chmod'd is still a usable key, and
    failing the run over it would be worse than the limitation it reports.

    Args:
        key_path: The private key.
    """
    try:
        key_path.chmod(0o600)
    except OSError:
        print("note: could not restrict the key file's permissions on this platform")


def _generate(openssl: str, cert_path: Path, key_path: Path) -> int:
    """Run openssl into a staging directory, then move the pair into place.

    STAGED RATHER THAN WRITTEN IN PLACE, for two reasons. Non-negotiable 5
    requires an atomic write for any file another process may read, and the
    surface and the shell both read these. And a --force run whose openssl
    call fails would otherwise have already destroyed the working pair it was
    replacing; staging means a failed run leaves the previous pair intact.

    THE PAIR IS NOT TWO-FILE ATOMIC and no filesystem primitive makes it so.
    Each rename is atomic individually; a crash between the two leaves a fresh
    key beside a stale certificate. That is why either file existing is enough
    to refuse a later run.

    Args:
        openssl: The resolved executable.
        cert_path: Where the certificate belongs.
        key_path: Where the key belongs.

    Returns:
        An exit code.
    """
    destination = cert_path.parent
    destination.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".make_cert-", dir=str(destination)))
    try:
        staged_cert = staging / cert_path.name
        staged_key = staging / key_path.name
        argv = cert_argv(staged_cert, staged_key, openssl)
        try:
            done = subprocess.run(
                argv,
                shell=False,
                capture_output=True,
                timeout=OPENSSL_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            print(f"openssl did not return within {OPENSSL_TIMEOUT_SECONDS}s; nothing was written")
            return EXIT_OPENSSL_FAILED

        if done.returncode != 0:
            reason = done.stderr.decode("utf-8", errors="replace").strip().splitlines()
            print(f"openssl exited {done.returncode}; nothing was written")
            if reason:
                print(f"  {redact(reason[-1])}")
            return EXIT_OPENSSL_FAILED

        if not staged_cert.is_file() or not staged_key.is_file():
            print("openssl reported success but wrote no pair; nothing was written")
            return EXIT_OPENSSL_FAILED

        _restrict(staged_key)
        _replace_with_retry(staged_key, key_path)
        _replace_with_retry(staged_cert, cert_path)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    print(f"wrote {redact(cert_path)}")
    print(f"wrote {redact(key_path)}")
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    """Mint the pair, or say precisely why it did not.

    Args:
        argv: Command line arguments, or None to read sys.argv.

    Returns:
        An exit code. See the module docstring for what each one means.
    """
    parser = argparse.ArgumentParser(
        description="Generate the self-signed certificate the local dashboard listens with.",
    )
    parser.add_argument(
        "--cert-dir",
        default=None,
        help=f"where to write the pair; overrides {ENV_CERT_DIR}",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing pair instead of refusing",
    )
    args = parser.parse_args(argv)

    destination = cert_dir(args.cert_dir)
    cert_path = destination / CERT_NAME
    key_path = destination / KEY_NAME

    # RESOLVED BEFORE ANYTHING IS CREATED, so a machine with no openssl is left
    # exactly as it was found rather than with an empty certificate directory
    # implying something happened.
    openssl = shutil.which("openssl")
    if openssl is None:
        print("openssl is not on PATH, so no certificate can be generated.")
        print("Install openssl, or add the one shipped with git to PATH, and run this again.")
        return EXIT_NO_OPENSSL

    already = [path for path in (cert_path, key_path) if path.exists()]
    if already and not args.force:
        print(f"refusing to overwrite {len(already)} existing file(s) in {redact(destination)}")
        print("The companion window may already have been told to trust this certificate.")
        print("Re-run with --force if replacing it is genuinely what you want.")
        return EXIT_REFUSED

    return _generate(openssl, cert_path, key_path)


if __name__ == "__main__":
    raise SystemExit(main())
