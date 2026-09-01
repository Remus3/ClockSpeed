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

A RAISE IS AN ECHO PATH TOO, WHICH IS WHAT CS-878 WAS. ``OSError.__str__``
appends ``filename`` and ``filename2`` verbatim, so an OSError this module lets
escape renders both absolute paths through the default excepthook - where no
print() runs and therefore no redact() does either. The measured case was the
rename retry re-raising the operating system's own error onto a destination the
operator had pointed at a home directory. Two independent barriers close it:
``_generate`` lets no OSError out, and ``_replace_with_retry`` raises a
path-free clone regardless of who catches it. The guard grades what today's
caller does; the clone grades what tomorrow's second caller gets.

Exit codes, distinct so a runbook can branch on them:

    0  the pair was written
    1  openssl is not on PATH
    2  openssl was found and failed, timed out, or produced nothing
    3  a pair is already there and --force was not given
    4  the pair could not be written into the destination

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

#: NAMED FOR THE OUTCOME RATHER THAN THE CAUSE, because the guard that returns
#: it spans every filesystem step ``_generate`` takes - creating the
#: destination, staging inside it, and moving the finished pair on. What they
#: share is that the destination did not end up holding a usable pair, and that
#: is what a runbook branching here needs to know. Before CS-878 this case
#: escaped as a traceback and exited 1, which this module documents as "openssl
#: is not on PATH" - so the one branch a runbook could take was the wrong one.
EXIT_WRITE_FAILED = 4

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


def _pathless_cause(exc: OSError) -> OSError:
    """Clone an OSError without the two fields that carry the path.

    THE SAME TWO-LINE IDIOM AS ``clockspeed/save/workdir.py::_pathless_cause``,
    replicated rather than imported: a script reaching into a private helper of
    the save layer is the seam violation CLAUDE.md section 2.1 names, and this
    file already imports the one public thing it needs from ``data``. That
    docstring carries the long form of the reasoning.

    ``OSError.__str__`` appends ``filename`` and ``filename2`` verbatim, and
    under this script those hold the operator's destination - a home directory
    whenever ``--cert-dir`` or ``CLOCKSPEED_CERT_DIR`` points at one, which
    ``cert_dir`` supports on purpose. Rebuilding from the two NAMED diagnostic
    fields carries errno and strerror across and leaves both filename fields
    unset, which closes that channel while keeping the reason the call failed.

    ``str()`` is the rendering that matters, because that is the one the
    traceback formatter uses. ``repr()`` would be a false clearance - it omits
    filename even on the leaking original.

    THE CALLER MUST RAISE THIS WITH ``from None``. Raising it inside an
    ``except`` block sets ``__context__`` to the original, and the formatter
    then renders that original in full underneath "During handling of the above
    exception" - both paths intact, on an exception whose own filename fields
    are empty. Measured before this was written, not anticipated.

    The two-argument form is deliberate. Supplying ``winerror`` as a fourth
    argument renders ``[WinError None]`` whenever the original carried none,
    which is worse than the errno it would replace. The errno-based subclass
    mapping still runs, so a PermissionError stays a PermissionError.

    Args:
        exc: The caught failure. ONLY ``errno`` and ``strerror`` are read.

    Returns:
        A new OSError of the same errno-mapped subclass, carrying no path.
    """
    return OSError(exc.errno, exc.strerror)


def _failure_detail(exc: OSError) -> str:
    """Render one OSError as an indented diagnostic line carrying no path.

    ONE PLACE TO BE RIGHT. Interpolating the exception itself is precisely the
    leak CS-878 closed, since ``str(exc)`` appends both filename fields, so the
    rendering lives here rather than being hand-written at each site that
    reports a failure.

    ``strerror`` is redacted even though no platform puts a path in it today.
    It is a string this module did not write, the promise in the module
    docstring is unconditional, and redact() is idempotent and never raises -
    so the check costs nothing and cannot be the part that rots.

    Args:
        exc: The failure being reported.

    Returns:
        The line to print, already indented under its headline.
    """
    reason = redact(exc.strerror) if exc.strerror else "no reason given"
    return f"  {type(exc).__name__}, errno {exc.errno}: {reason}"


def _replace_with_retry(source: Path, target: Path) -> None:
    """Move ``source`` onto ``target``, retrying a Windows sharing violation.

    ONLY PermissionError IS RETRIED, and that is unchanged: a scanner or an
    indexer can still hold a handle on a file closed moments ago, while every
    other OSError is a real failure with nothing to wait for.

    WHAT LEAVES THIS FUNCTION IS NEVER THE ORIGINAL (CS-878).
    ``source.replace(target)`` raises an OSError whose ``str()`` appends both
    absolute paths, and re-raising it put the operator's destination in front
    of the default excepthook, where nothing redacts. Both exits now raise a
    path-free clone, with ``from None`` so the original is not rendered as the
    suppressed context either - see :func:`_pathless_cause`.

    THE SECOND HANDLER IS NOT REDUNDANT. Only PermissionError reaches the retry
    clause, so every other OSError used to walk straight out of this loop still
    carrying both paths - and a sharing violation is a Windows spelling of a
    problem other platforms report differently. UNMEASURED, AND SAID SO: the
    machine that measured CS-878 runs Windows, where a rename onto an occupied
    name raises PermissionError; that a POSIX kernel reports it as EISDIR
    instead is read from the errno tables and has not been run here. The
    handler is written to need no answer to that question.

    Args:
        source: The staged file.
        target: Where it belongs.

    Raises:
        OSError: The rename kept failing. It carries errno and strerror, and
            no path by either channel.
    """
    for attempt in range(_RENAME_ATTEMPTS):
        try:
            source.replace(target)
        except PermissionError as exc:
            if attempt == _RENAME_ATTEMPTS - 1:
                raise _pathless_cause(exc) from None
            time.sleep(_RENAME_PAUSE_SECONDS)
        except OSError as exc:
            raise _pathless_cause(exc) from None
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

    NO OSError LEAVES THIS FUNCTION (CS-878). Every filesystem call it makes -
    creating the destination, staging inside it, launching openssl, and the two
    renames - raises an OSError carrying the path it could not use, and there
    is no handler between here and the interpreter: ``main`` returns this call
    bare and the module entry is ``raise SystemExit(main())``. One guard spans
    the lot rather than three, because what they share is the only thing a
    caller can act on - the destination does not hold a usable pair - and three
    hand-written reports would be three chances to interpolate the exception.

    Args:
        openssl: The resolved executable.
        cert_path: Where the certificate belongs.
        key_path: Where the key belongs.

    Returns:
        An exit code. EXIT_WRITE_FAILED for any filesystem refusal, already
        reported on stdout with its errno and no path.
    """
    destination = cert_path.parent
    staging: Path | None = None
    try:
        destination.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".make_cert-", dir=str(destination)))
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
    except OSError as exc:
        print(f"the pair was not written into {redact(destination)}")
        print(_failure_detail(exc))
        print("The destination may hold half a pair; --force replaces whatever is there.")
        return EXIT_WRITE_FAILED
    finally:
        if staging is not None:
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
