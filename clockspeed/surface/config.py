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

AND THAT IS ENFORCED BY THE CONSTRUCTOR RATHER THAN BY PROSE. :class:`ConfigError`
takes a :class:`ConfigFault` - a member of a closed set declared here - and never
a string, so :func:`config_refusal` is the only thing that can decide what the
operator reads. The sentence above used to be the whole control, and a sentence
is a control that holds exactly as long as every future raise site has read it:
``ConfigError(str(path))`` satisfied the old signature, type-checked, and would
have written a home directory to stderr. It does not type-check now and raises at
construction if it is forced through anyway. ``clockspeed/surface/server.py``
states the same reasoning for ``BindError`` and ``bind_refusal``, and this is the
same shape over a four-member vocabulary instead of over a port number.

AND THE MESSAGE WAS STILL NOT THE WHOLE CHANNEL (CS-857). A refusal chained with
``raise X from exc`` puts the CAUSE's own text into the formatted traceback, and
``OSError.__str__`` appends ``filename``. So a wrapper hardened by construction
went on handing the record path to the default excepthook through the cause
beside it, which the paragraph above could not see because it reasons only about
what the wrapper says. :func:`_pathless_cause` closes that, and
``tests/surface/test_config.py`` section (f) grades it by reading what a real
interpreter really printed - the only place the context channel is visible.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "CERT_DIR_ENV",
    "CERT_NAME",
    "DEFAULT_CERT_DIRNAME",
    "FAULT_NOT_A_MEMBER",
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
    "ConfigFault",
    "ServerConfig",
    "allocated_port",
    "cert_dir",
    "config_refusal",
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

#: What a caller who passed something other than a :class:`ConfigFault` is
#: refused with. A PROGRAMMING error rather than a configuration one, so it is a
#: ``TypeError`` and not a :class:`ConfigError` - but it is a fixed line for the
#: identical reason every line above is one. MEASURED, not assumed: letting the
#: mapping lookup refuse instead raised ``KeyError('C:/Users/<account>/...')``
#: for exactly the call this vocabulary exists to stop -
#: ``ConfigError(str(path))`` - so the guard rail's own failure path was the
#: leak. It quotes nothing it was handed.
FAULT_NOT_A_MEMBER: Final = "a configuration refusal must name a ConfigFault member"


class ConfigFault(Enum):
    """WHICH configuration refusal happened, as a value no caller can author.

    A CLOSED VOCABULARY RATHER THAN A STRING PARAMETER, and the difference is
    the whole control. :class:`ConfigError` used to take the message itself, so
    what an operator read was decided at each raise site; every site in this
    module passed a constant above, and the class docstring recorded that as a
    promise. A promise about five sites is not a property of the type. The
    member below is an identifier and carries none of the text - the text is
    :func:`config_refusal`'s alone - so the day a sixth raise site wants to name
    the file it refused, there is no argument it can pass to do it.

    The values are keys, deliberately not sentences: a member whose value WAS
    the refusal would put the line in two places, and CLAUDE.md section 4 names
    a restated fact as one that drifts.
    """

    RECORD_UNREADABLE = "record_unreadable"
    RECORD_MALFORMED = "record_malformed"
    PORT_NOT_AN_INTEGER = "port_not_an_integer"
    PORT_OUT_OF_RANGE = "port_out_of_range"


#: Fault to the one line it is spoken as. The four constants above are still the
#: only spelling of each sentence; this maps onto them rather than repeating
#: them.
_REFUSALS: Final[Mapping[ConfigFault, str]] = MappingProxyType(
    {
        ConfigFault.RECORD_UNREADABLE: RECORD_UNREADABLE,
        ConfigFault.RECORD_MALFORMED: RECORD_MALFORMED,
        ConfigFault.PORT_NOT_AN_INTEGER: PORT_NOT_AN_INTEGER,
        ConfigFault.PORT_OUT_OF_RANGE: PORT_OUT_OF_RANGE,
    }
)


def config_refusal(fault: ConfigFault) -> str:
    """The one line an operator reads when the configuration would not resolve.

    A MODULE-LEVEL FUNCTION RATHER THAN A METHOD, for the reason
    ``clockspeed/surface/server.py`` gives about :func:`bind_refusal` there: the
    text has ONE author, and neither the raise site nor the process's handler
    has to render an exception OBJECT to reach it. ``str()`` on a caught object
    is what its RUNTIME type decides, and today's runtime type is not a promise
    about tomorrow's - widen one ``except`` clause to ``OSError`` and the same
    spelling appends the path the call failed on, which on this machine carries
    the account name (non-negotiable 12). ``tests/test_exception_rendering.py``
    refuses that shape categorically, and this is the spelling that satisfies
    it: a named field of a closed type, mapped to text this module owns.

    Args:
        fault: Which refusal to speak. A member of :class:`ConfigFault` and
            never text - see that class for why the parameter is not a string.

    Returns:
        The refusal, with no trailing newline. Byte-identical to the matching
        module constant, which is where each sentence is actually spelled.

    Raises:
        TypeError: ``fault`` is not a member of :class:`ConfigFault`. CHECKED
            EXPLICITLY RATHER THAN LEFT TO THE MAPPING, because a ``KeyError``
            renders the key - so the one call this vocabulary exists to stop,
            ``ConfigError(str(path))``, would have leaked the path through the
            guard rail's own failure. :data:`FAULT_NOT_A_MEMBER` quotes nothing.
        KeyError: A member was added to :class:`ConfigFault` without a line in
            :data:`_REFUSALS`. Its key is a member repr this module authored, so
            that residual carries no caller value and is left loud.
    """
    if not isinstance(fault, ConfigFault):
        raise TypeError(FAULT_NOT_A_MEMBER)
    return _REFUSALS[fault]


class ConfigError(Exception):
    """The dashboard's configuration could not be resolved.

    Carries one of the fixed lines above and never a path, a filename or a
    fragment of whatever it refused - now BY CONSTRUCTION rather than by the
    discipline of each raise site. See the module docstring for why.

    Attributes:
        fault: Which refusal this is. The NAMED FIELD that
            ``clockspeed/surface/__main__.py`` renders in place of the object,
            exactly as ``server.run`` renders ``BindError.port``.
        reason: The fixed line that fault is spoken as, and what ``str()`` on
            this exception yields. Held as a field so a reader of a traceback
            does not have to know the mapping to know what was said.
    """

    def __init__(self, fault: ConfigFault) -> None:
        """Build the refusal from the fault, and from nothing the caller wrote.

        Args:
            fault: Which refusal happened.
        """
        self.fault = fault
        self.reason = config_refusal(fault)
        super().__init__(self.reason)


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
        raise ConfigError(ConfigFault.PORT_OUT_OF_RANGE)
    return value


def _pathless_cause(exc: OSError) -> OSError:
    """Clone an OSError without the two fields that carry the path.

    THE SAME TWO-LINE IDIOM AS ``clockspeed/save/workdir.py::_pathless_cause``,
    replicated rather than imported, for the reason :func:`repo_root` above
    already records about a different helper: ``surface/`` reaching into a
    private underscore name of ``save/`` is the seam violation CLAUDE.md section
    2.1 names and ruff's SLF rules exist to catch, and this module deliberately
    imports nothing from another package of this tree at all. That docstring,
    and ``scripts/make_cert.py``'s copy of it, carry the long form of the
    reasoning. THE FOURTH COPY IS A PRICED DUPLICATE RATHER THAN AN UNEXAMINED
    ONE, and this paragraph is that price. It used to call a single shared owner
    the correct repair and stop there; CS-885 then MEASURED that repair and
    DECLINED it, so a recommendation outlived the question it answered. The
    census clears a cause slot only when the slot is a bare-name call to a
    function defined at module level in THAT module, so routing a site through
    an owner it has to import - bare name or dotted alike - drops it from
    ``closed-pathless`` to ``unproven``; every relying site in this tree is
    written that same way, so they all drop at once. Buying them back would mean
    teaching the clearance to resolve imported names across modules, over
    aliases, dotted calls, re-exports and shadowing - a WIDENING of the
    predicate that ISSUES the clearance, on the privacy channel, in the one
    direction it must never err. So the duplication stays,
    ``tests/pathless_clone_guard.py`` is what makes it safe by comparing the
    copies every run, and ``tests/test_pathless_clone_agreement.py`` holds this
    paragraph to the live census rather than to any number written into it.

    WHY A CLEAN WRAPPER WAS NOT ENOUGH. ``raise X from exc`` makes the CAUSE's
    own text part of the formatted traceback, and ``OSError.__str__`` appends
    ``filename`` and ``filename2`` verbatim. :func:`config_refusal` above had
    already reasoned that widening an ``except`` clause to ``OSError`` makes the
    same spelling append the path the call failed on; the clause in
    :func:`allocated_port` IS that clause, and until CS-857 this module handed
    the record path to the renderer through the cause it chained to rather than
    through a message of its own. MEASURED rather than anticipated: a
    ``read_bytes`` failure raises ``FileNotFoundError`` with ``filename`` set,
    and the default excepthook printed it.

    Rebuilding from the two NAMED diagnostic fields carries errno and strerror
    across and leaves both filename fields unset, which closes that channel while
    keeping the reason the read failed. That reason is not a nicety: the fixed
    line above deliberately says neither which file nor why, so whether the
    record is ABSENT or present and UNREADABLE - different faults with different
    remedies - is tellable apart here or nowhere.

    ``str()`` is the rendering measured, because that is the one the traceback
    formatter uses. ``repr()`` would have been a false clearance - it omits
    filename even on the leaking original.

    THE CALLER PASSES THIS AS THE ``from`` OPERAND, and that is what suppresses
    the context. ``raise X from Y`` sets ``__suppress_context__``, so the
    original is not rendered underneath "During handling of the above
    exception"; a bare ``raise _pathless_cause(exc)`` would leave that channel
    open with both paths intact, which ``scripts/make_cert.py`` records having
    measured.

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
            or the content, AND NEITHER IS CHAINED TO A CAUSE THAT DOES:
            :func:`_pathless_cause` states why the message alone was not the
            whole channel. The malformed cause needs no such treatment - a
            decode or JSON failure carries no filename field to begin with -
            so it is chained directly and that asymmetry is deliberate.
    """
    path = ports_record_path() if record is None else record
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ConfigError(ConfigFault.RECORD_UNREADABLE) from _pathless_cause(exc)
    try:
        payload = json.loads(raw.decode("ascii"))
        base = payload[PORTS_RECORD_BASE_KEY]
    except (UnicodeDecodeError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ConfigError(ConfigFault.RECORD_MALFORMED) from exc
    if isinstance(base, bool) or not isinstance(base, int):
        raise ConfigError(ConfigFault.RECORD_MALFORMED)
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
            raise ConfigError(ConfigFault.PORT_NOT_AN_INTEGER) from exc
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
