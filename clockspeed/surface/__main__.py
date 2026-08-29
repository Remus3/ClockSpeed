"""``python -m clockspeed.surface`` - the composition root for the dashboard.

Owns (BOOTSTRAP.md section 7.1): the process. It reads the configuration, builds
the providers, assembles the route table, hands all three to the server and turns
what comes back into a process exit code. It is the only module in this package
that touches ``sys.argv``, ``sys.exit`` or the real environment.

IT COMPUTES NOTHING AND DECIDES NOTHING ABOUT A RESPONSE. Every question a
request can ask is answered below this file; every question the OPERATOR asks -
which port, which certificate, whether to look for a save - is answered here and
nowhere else. That split is why no endpoint module reads an environment variable.

THE WORLD IS AUTO-DETECTED ON STARTUP, and the flag turns detection OFF rather
than on. ``python -m clockspeed.surface`` with no arguments finds the newest save
on this machine and serves it, because a dashboard that requires an argument to
show anything is a dashboard the operator has to be taught to use. Detection is
LAZY - the provider stores callables and reads nothing until ``/api/world`` is
requested - so a machine with no save and no game still starts, still binds, and
still answers every endpoint. The absence surfaces as a 503 from ``/api/world``
and as ``absent`` in the health body. It is never a crash and never a refusal to
start, because "there is no save here" is a true statement about a working
system rather than a failure of one.

A BIND REFUSAL ENDS THE PROCESS AND NAMES THE PORT. No second port is ever
tried. The reasoning is in ``clockspeed/surface/server.py``, and the operational
half of it is this: an operator who asked for a port and got a different one has
a dashboard they cannot find, a companion window that will not connect, and no
message saying why. Exiting with a distinct code and the number in the message
is what lets ``docs/OPERATIONS.md`` say what to do next.

THE EXIT CODES ARE THE INTERFACE. ``clockspeed/surface/server.py`` owns the three
it can produce; this module adds exactly one, for the configuration it resolves
before the server is reachable at all. They are distinct so a runbook can branch
on them, and they are documented in ``docs/OPERATIONS.md``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

from clockspeed.surface import server
from clockspeed.surface.api.routes import METHOD_BOUNDARY_ROUTES, build_routes
from clockspeed.surface.config import ConfigError, config_refusal, load_config
from clockspeed.surface.providers import InstalledRegistryProvider, SaveWorldProvider, StaticAssets

if TYPE_CHECKING:
    from collections.abc import Sequence

    from clockspeed.save.world import WorldModel
    from clockspeed.surface.api import contract

__all__ = [
    "EXIT_CONFIG",
    "NO_WORLD_FLAG",
    "main",
    "parse_args",
    "world_provider",
]

#: The configuration would not resolve, so the server was never reached. Distinct
#: from the three ``clockspeed/surface/server.py`` publishes, and deliberately 1:
#: it is the conventional "the invocation was wrong" code, and this is the only
#: refusal that happens before anything is bound or opened.
EXIT_CONFIG: Final = 1

#: The flag that turns startup save detection off. Named as a constant because
#: the test suite drives it and a string typed twice is a string that drifts.
NO_WORLD_FLAG: Final = "--no-world"

#: What the program calls itself in its own help text. Spelled rather than taken
#: from ``sys.argv[0]``, which under ``-m`` renders the absolute path of this
#: file - and that path contains the Windows account name (non-negotiable 3).
PROGRAM: Final = "python -m clockspeed.surface"

_DESCRIPTION: Final = "Serve the local HTTPS dashboard and JSON API on this machine."

_EPILOG: Final = (
    "The port is read from config/ports.json unless --port or "
    "CLOCKSPEED_DASHBOARD_PORT overrides it. Mint the certificate with "
    "scripts/make_cert.py before the first run."
)


class _NoWorld:
    """A world provider for a run started with save detection turned off.

    Reads nothing and finds nothing, so ``/api/world`` answers 503 and the health
    body reports the world absent - the same two answers a machine with no save
    produces, reached deliberately instead of by circumstance.

    NOT A DATACLASS AND HOLDS NO STATE, so it is outside the population
    ``tests/repr_rendering_guard.py`` grades and can render nothing.
    """

    def world(self) -> None:
        """The current world.

        Returns:
            None, always: this provider was asked not to look. Declared
            ``None`` rather than ``object | None`` because that is what it
            actually returns; the wider spelling was written to match a
            provider parameter that was itself too wide.
        """
        return


def world_provider(*, auto_detect: bool) -> contract.WorldProvider[WorldModel]:
    """Choose between looking for a save on this machine and not looking.

    Args:
        auto_detect: True to resolve the newest save at request time, which is
            the default. False to answer "no world" without touching the disk.

    Returns:
        The provider. Either way it is lazy: nothing is read here.
    """
    if not auto_detect:
        return _NoWorld()
    return SaveWorldProvider()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the operator's arguments.

    Separated from :func:`main` so the defaults are gradeable without starting a
    process - "the world is detected unless the operator says otherwise" is a
    ruling, and a ruling that is only observable by running a server is one
    nothing can hold to.

    Args:
        argv: The arguments, or None for ``sys.argv[1:]``.

    Returns:
        The parsed namespace. ``--help`` exits 0 from inside this call, before
        any path on this machine is resolved.
    """
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description=_DESCRIPTION,
        epilog=_EPILOG,
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="the port to bind; overrides the allocation record and the environment",
    )
    parser.add_argument(
        "--cert-dir",
        type=str,
        default=None,
        help="where the certificate pair lives; overrides CLOCKSPEED_CERT_DIR",
    )
    parser.add_argument(
        NO_WORLD_FLAG,
        dest="auto_detect_world",
        action="store_false",
        default=True,
        help="do not look for a save on startup; /api/world then answers 503",
    )
    return parser.parse_args(argv)


def _certificate_dir(declared: str | None) -> Path | None:
    """Turn the declared certificate directory into a path, or None.

    Args:
        declared: What the operator typed, or None.

    Returns:
        The path, or None to let the configuration resolve it.
    """
    if declared is None:
        return None
    return Path(declared)


def main(argv: Sequence[str] | None = None) -> int:
    """Start the dashboard, serve until stopped, and return the exit code.

    Args:
        argv: The arguments, or None for ``sys.argv[1:]``.

    Returns:
        ``server.EXIT_OK`` on a clean stop, :data:`EXIT_CONFIG` when the
        configuration would not resolve, ``server.EXIT_CERTIFICATE`` when the
        pair would not load, or ``server.EXIT_BIND_FAILED`` when the port could
        not be taken. No second port is ever attempted.
    """
    args = parse_args(argv)
    try:
        config = load_config(
            requested_port=args.port,
            certificate_dir=_certificate_dir(args.cert_dir),
        )
    except ConfigError as exc:
        # THE NAMED FIELD, NEVER THE OBJECT, and that is a rule about the
        # RUNTIME type rather than about today's message. `f"{exc}"` leaks
        # nothing as this module stands - every `ConfigError` carries one of four
        # lines `clockspeed/surface/config.py` owns - but the value `str()`
        # renders is whatever the caught object turns out to BE, so widening this
        # `except` to `OSError` would turn the same spelling into a home-path
        # leak (non-negotiable 12). `config_refusal` is the identical idiom
        # `server.run` uses for `bind_refusal(exc.port)` one layer down.
        sys.stderr.write(f"{config_refusal(exc.fault)}\n")
        return EXIT_CONFIG

    routes = build_routes(
        world_provider(auto_detect=args.auto_detect_world),
        InstalledRegistryProvider(),
    )
    assets = StaticAssets(config.web_dir, server.ASSET_NAMES)
    return server.run(config, routes + METHOD_BOUNDARY_ROUTES, assets)


if __name__ == "__main__":
    sys.exit(main())
