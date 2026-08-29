"""Where the dashboard listens, and what it listens with.

Owns (BOOTSTRAP.md section 7.1): the resolution of the listening address, the
listening port, the certificate pair and the dashboard asset directory into the
one frozen value the server is handed.

THE PORT NUMBER IS NOT IN THIS FILE AND MUST NEVER BE. The parent package states
the rule - "The port is ALLOCATED, recorded once in the project configuration,
and read from there. It is not restated in code (CONVENTIONS.md section 2)" -
and ``config/ports.json`` is that record. This module reads
:data:`PORTS_RECORD_BASE_KEY` out of it. The allocation MOVED once already, and a
number spelled here would have been a second, silently stale copy of it;
``tests/surface/test_config.py`` sweeps both this module and the whole surface
test package for an integer literal anywhere in the allocated band so that a
second copy cannot be introduced without turning the suite red.

PRECEDENCE IS STATED RATHER THAN LEFT TO WHICHEVER THE READER ASSUMES: an
explicit request beats :data:`PORT_ENV`, which beats the record. Nothing falls
back past the record - a port that resolves to something other than what was
asked for is a dashboard the companion window cannot find, and the server module
refuses to move to a different port for the same reason.

THIS MODULE READS ONE FILE AND WRITES NONE. It is one of exactly two modules in
this package permitted to touch the filesystem at all, the other being
``providers.py``; ``tests/surface/test_server.py`` pins that allow-list and
separately pins that NO module in the package writes anything. The one file read
here is this repository's own tracked configuration record - not a save, not the
game install, and nothing derived from either.

WHY EVERY REFUSAL IS A FIXED LINE. The record path is derived from this file's
own location, but :data:`CERT_DIR_ENV` can point anywhere, including inside a
home directory, and a home path is personal data under non-negotiable 3. So no
message built here quotes a path, a filename or any fragment of a file it
refused - the same idiom ``clockspeed/save/world.py`` and
``clockspeed/data/locate.py`` state in prose, and the same one
``contract.py`` applies to a request path.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "CERT_DIR_ENV",
    "CERT_NAME",
    "DEFAULT_CERT_DIRNAME",
    "HIGHEST_PORT",
    "KEY_NAME",
    "LOOPBACK",
    "LOWEST_PORT",
    "PORTS_RECORD_BASE_KEY",
    "PORTS_RECORD_PARTS",
    "PORT_ENV",
    "PORT_NOT_AN_INTEGER",
    "PORT_OUT_OF_RANGE",
    "RECORD_MALFORMED",
    "RECORD_UNREADABLE",
    "WEB_DIRNAME",
    "ConfigError",
    "ServerConfig",
    "allocated_port",
    "cert_dir",
    "default_web_dir",
    "load_config",
    "ports_record_path",
    "repo_root",
    "resolve_port",
]


# ---------------------------------------------------------------------------
# The address
# ---------------------------------------------------------------------------

#: The ONLY address this server ever binds. Not a default and not a preference:
#: the dashboard reads a local save and answers questions about it, so a
#: listener reachable from another machine is a disclosure channel that no
#: amount of later authentication makes safe. The server module asserts this
#: value rather than accepting an address argument.
LOOPBACK: Final = "127.0.0.1"

#: Overrides the record's allocation. Beaten in turn by an explicit request.
PORT_ENV: Final = "CLOCKSPEED_DASHBOARD_PORT"

#: The allocation record, relative to the repository root. The record is the
#: single owner of the number (CLAUDE.md section 4); this is the path to it.
PORTS_RECORD_PARTS: Final = ("config", "ports.json")

#: The key inside that record holding the dashboard's allocated port.
PORTS_RECORD_BASE_KEY: Final = "base"

#: What the transport admits. NOT an allocation - the record owns the
#: allocation, and these two are the range any port at all has to sit inside.
#: Zero is admitted deliberately: it is what asks the kernel for an ephemeral
#: port, and every test in this package binds it rather than the real one.
LOWEST_PORT: Final = 0
HIGHEST_PORT: Final = 65535


# ---------------------------------------------------------------------------
# The certificate pair
# ---------------------------------------------------------------------------
#
# SEAM COLLISION, RECORDED RATHER THAN PAPERED OVER. ``scripts/make_cert.py``
# WRITES this pair and already spells all four names. This module READS the pair
# and so spells them a second time, which is exactly the restated fact CLAUDE.md
# section 4 warns will drift. The correct repair is to make THIS module the owner
# and have the script import from it, and that script is not on this slice's
# write-list. Until it is, ``test_config.py`` parses the script's own literals
# out of its AST and asserts the two spellings agree, so the drift is a red test
# rather than a dashboard that cannot find the certificate it was handed.

#: The certificate and its key, named so the pair is obvious in a listing.
CERT_NAME: Final = "dashboard.cert.pem"
KEY_NAME: Final = "dashboard.key.pem"

#: Overrides the default destination. May point inside a home directory, which
#: is why nothing built here renders it.
CERT_DIR_ENV: Final = "CLOCKSPEED_CERT_DIR"

#: The default destination, relative to the repository root. ``.gitignore``
#: carries ``/certs/`` plus ``*.pem``, so nothing there can be committed.
DEFAULT_CERT_DIRNAME: Final = "certs"

#: The dashboard assets, inside this package. Absent until the asset slice
#: lands, and its absence is a 404 rather than a crash - see ``providers.py``.
WEB_DIRNAME: Final = "web"


# ---------------------------------------------------------------------------
# Refusals. Each is a FIXED line and none is ever built from content.
# ---------------------------------------------------------------------------

RECORD_UNREADABLE: Final = (
    "the port allocation record could not be read; it belongs at config/ports.json"
)
RECORD_MALFORMED: Final = (
    "the port allocation record does not carry an integer base port under the key 'base'"
)
PORT_NOT_AN_INTEGER: Final = "a declared dashboard port must be a base-ten integer"
PORT_OUT_OF_RANGE: Final = "a dashboard port must sit between 0 and 65535 inclusive"


class ConfigError(Exception):
    """The dashboard's configuration could not be resolved.

    Carries one of the fixed lines above and never a path, a filename or a
    fragment of whatever it refused. See the module docstring for why.
    """


# ---------------------------------------------------------------------------
# The resolved value
# ---------------------------------------------------------------------------


@dataclass(frozen=True, repr=False)
class ServerConfig:
    """Everything the server needs to bind and to answer, resolved once.

    ``repr=False`` PLUS A HAND-WRITTEN ``__repr__`` IS MANDATORY HERE, not a
    style choice. Three fields are annotated ``Path``, and
    ``tests/repr_rendering_guard.py`` grades every shipped class holding one
    under its rule R2: a generated ``__repr__`` renders a ``Path`` in full, so
    ``WindowsPath('C:/Users/<account>/...')`` reaches a log or a traceback with
    no save ever being parsed, defeating non-negotiable 3. The guard also grades
    a hand-written method that renders the field anyway, which is why the one
    below names neither the certificate pair nor the asset directory.

    Attributes:
        host: The bind address, always :data:`LOOPBACK`.
        port: The resolved port. Zero means the kernel picks an ephemeral one.
        cert_path: The certificate to listen with. Not required to exist here;
            the server refuses at bind time with a fixed line if it does not.
        key_path: Its private key. Never rendered, never logged, never read by
            anything in this package other than the TLS context.
        web_dir: Where the dashboard assets live. Its absence is a 404 rather
            than an error, because the asset slice can land after this one.
    """

    host: str
    port: int
    cert_path: Path
    key_path: Path
    web_dir: Path

    def __repr__(self) -> str:
        """Render the address and withhold every path.

        Returns:
            The safe rendering: the two fields that are not carriers.
        """
        return f"{type(self).__name__}(host={self.host!r}, port={self.port})"


# ---------------------------------------------------------------------------
# Locations, all derived from this file rather than from a working directory
# ---------------------------------------------------------------------------


def repo_root() -> Path:
    """Return the repository root, derived from this file's own location.

    Mirrors ``clockspeed/data/locate.py`` rather than importing its private
    helper: reaching for another module's underscore name is the seam violation
    ruff's SLF rules exist to catch, and two lines of duplication is the
    cheaper of the two faults.

    Returns:
        The directory two levels above ``clockspeed/surface/``.
    """
    return Path(__file__).resolve().parents[2]


def ports_record_path() -> Path:
    """Return where the port allocation is recorded.

    Returns:
        ``config/ports.json`` under the repository root. Not required to exist;
        :func:`allocated_port` is what refuses a missing one.
    """
    return repo_root().joinpath(*PORTS_RECORD_PARTS)


def default_web_dir() -> Path:
    """Return where the dashboard assets live.

    Returns:
        The ``web`` directory inside this package. Not required to exist.
    """
    return Path(__file__).resolve().parent / WEB_DIRNAME


def cert_dir(env: Mapping[str, str] | None = None) -> Path:
    """Resolve where the certificate pair lives.

    Args:
        env: The environment to read, or None for the real one. Passing a
            mapping is how a test overrides without mutating the process.

    Returns:
        The directory named by :data:`CERT_DIR_ENV`, or ``certs`` beside the
        repository. Not created and not required to exist.
    """
    environment = os.environ if env is None else env
    declared = (environment.get(CERT_DIR_ENV) or "").strip()
    if declared:
        return Path(declared).expanduser()
    return repo_root() / DEFAULT_CERT_DIRNAME


# ---------------------------------------------------------------------------
# The port
# ---------------------------------------------------------------------------


def _checked_port(value: int) -> int:
    """Return the port, or refuse one the transport cannot carry.

    Args:
        value: The candidate.

    Returns:
        The port, unchanged.

    Raises:
        ConfigError: It sits outside the transport's range. The message states
            the range and does NOT quote the value - a rejected value is
            caller-chosen text, and this module quotes none of it.
    """
    if not LOWEST_PORT <= value <= HIGHEST_PORT:
        raise ConfigError(PORT_OUT_OF_RANGE)
    return value


def allocated_port(record: Path | None = None) -> int:
    """Read the allocated port out of the record that owns it.

    Args:
        record: The record to read, or None for :func:`ports_record_path`.

    Returns:
        The integer under :data:`PORTS_RECORD_BASE_KEY`.

    Raises:
        ConfigError: The record could not be read, did not parse, or carries no
            integer base. Two distinct fixed lines, so "the file is not there"
            and "the file is not what it should be" stay tellable apart -
            different faults with different remedies. Neither quotes the path
            or the content.
    """
    path = ports_record_path() if record is None else record
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ConfigError(RECORD_UNREADABLE) from exc
    try:
        payload = json.loads(raw.decode("ascii"))
        base = payload[PORTS_RECORD_BASE_KEY]
    except (UnicodeDecodeError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ConfigError(RECORD_MALFORMED) from exc
    if isinstance(base, bool) or not isinstance(base, int):
        raise ConfigError(RECORD_MALFORMED)
    return _checked_port(base)


def resolve_port(
    *,
    requested: int | None = None,
    env: Mapping[str, str] | None = None,
    record: Path | None = None,
) -> int:
    """Resolve the port the dashboard listens on, in the stated order.

    An explicit request beats :data:`PORT_ENV`, which beats the record. A
    declared value that does not parse is REFUSED rather than skipped: silently
    ignoring an override leaves the operator looking at a dashboard on a port
    they did not ask for and cannot see was overridden, which is the same
    "plausible rather than honest" failure the server module refuses a port
    fallback for.

    Args:
        requested: An explicit port, typically from ``--port``. None means
            nothing was requested.
        env: The environment to read, or None for the real one.
        record: The allocation record, or None for the real one.

    Returns:
        The resolved port.

    Raises:
        ConfigError: A declared value is not a base-ten integer, or sits outside
            the transport's range, or the record could not be resolved.
    """
    if requested is not None:
        return _checked_port(requested)
    environment = os.environ if env is None else env
    declared = (environment.get(PORT_ENV) or "").strip()
    if declared:
        try:
            parsed = int(declared, 10)
        except ValueError as exc:
            raise ConfigError(PORT_NOT_AN_INTEGER) from exc
        return _checked_port(parsed)
    return allocated_port(record)


# ---------------------------------------------------------------------------
# The whole value
# ---------------------------------------------------------------------------


def load_config(
    *,
    requested_port: int | None = None,
    env: Mapping[str, str] | None = None,
    record: Path | None = None,
    certificate_dir: Path | None = None,
) -> ServerConfig:
    """Resolve everything the server needs into one frozen value.

    Args:
        requested_port: An explicit port, typically from ``--port``.
        env: The environment to read, or None for the real one.
        record: The allocation record, or None for the real one.
        certificate_dir: Where the pair lives, or None to resolve it from
            :data:`CERT_DIR_ENV` and then the default.

    Returns:
        The configuration.

    Raises:
        ConfigError: The port could not be resolved. Nothing else here can
            fail - a missing certificate is the server's refusal to make, at
            bind time, where it can say so with the port in hand.
    """
    directory = cert_dir(env) if certificate_dir is None else certificate_dir
    return ServerConfig(
        host=LOOPBACK,
        port=resolve_port(requested=requested_port, env=env, record=record),
        cert_path=directory / CERT_NAME,
        key_path=directory / KEY_NAME,
        web_dir=default_web_dir(),
    )
